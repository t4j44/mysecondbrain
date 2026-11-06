# Windows-only private-input tests. All values and files are synthetic.
$ErrorActionPreference = 'Stop'
$inputScript = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../private_recovery_input.ps1'))
$python = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../apps/api/.venv/Scripts/python.exe'))
$verifier = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../verify_private_setup.py'))
$folder = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'secure/SecondBrainRecovery'
$prefix = 'synthetic-guards-' + [Guid]::NewGuid().ToString('N')
$target = Join-Path $folder ($prefix + '.dpapi')
$corrupt = Join-Path $folder ($prefix + '-corrupt.dpapi')
$checks = @{}
try {
    . $inputScript -Destination $target -SelfTestClick -LoadFunctionsOnly
    $urlValue = 'postgresql://postgres.rpkjmdrralzxhdsgceal:synthetic@aws-0-synthetic.pooler.supabase.com:5432/postgres'
    $phraseValue = 'Synthetic unicode phrase ' + [char]0x00a3 + [char]0x03bb
    Save-PrivateSetup $urlValue $phraseValue $target
    $proof = Assert-PrivateFile $target $urlValue $phraseValue
    $checks.final_path_exists = [IO.File]::Exists($target)
    $checks.final_dpapi_read_back = ($proof.final_read_back -eq 'PASS')
    $checks.owner_only_permissions = ($proof.private_permissions -eq 'PASS')
    $checks.directory_inheritance_disabled = (Get-Acl -LiteralPath $folder).AreAccessRulesProtected
    $readerOutput = & $python $verifier --path $target --allow-synthetic
    $checks.independent_backup_reader = ($LASTEXITCODE -eq 0 -and ($readerOutput | ConvertFrom-Json).windows_decryption -eq 'PASS')

    $before = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    $rejected = $false
    try { Save-PrivateSetup $urlValue 'Different synthetic phrase only' $target } catch { $rejected = $true }
    $checks.no_overwrite = ($rejected -and $before -ceq (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)

    $rejected = $false
    try { Assert-PrivateFile ($target + '.missing') $urlValue $phraseValue | Out-Null } catch { $rejected = $true }
    $checks.missing_final_file_rejected = $rejected

    [byte[]]$damaged = [IO.File]::ReadAllBytes($target)
    $damaged[$damaged.Length - 1] = $damaged[$damaged.Length - 1] -bxor 1
    [IO.File]::WriteAllBytes($corrupt, $damaged)
    $rejected = $false
    try { Assert-PrivateFile $corrupt $urlValue $phraseValue | Out-Null } catch { $rejected = $true }
    $checks.corrupt_final_file_rejected = $rejected
    $ignoredOutput = & $python $verifier --path $corrupt --allow-synthetic
    $checks.independent_reader_rejects_corruption = ($LASTEXITCODE -ne 0)

    $ignoredOutput = & $python $verifier --path $target
    $checks.synthetic_rejected_for_real_backup = ($LASTEXITCODE -ne 0)
    $unsafe = Join-Path ([IO.Path]::GetDirectoryName($inputScript)) 'unsafe-synthetic.dpapi'
    $rejected = $false
    try {
        $ignoredOutput = & powershell.exe -NoProfile -STA -File $inputScript -Destination $unsafe -SelfTestClick 2>$null
        $rejected = ($LASTEXITCODE -ne 0)
    } catch { $rejected = $true }
    $checks.git_folder_target_rejected = ($rejected -and -not [IO.File]::Exists($unsafe))

    $checks.url_password_only_accepted = ((Resolve-PrivateConnection $urlValue '') -ceq $urlValue)
    $checks.same_password_twice_accepted = ((Resolve-PrivateConnection $urlValue 'synthetic') -ceq $urlValue)
    $placeholder = $urlValue.Replace(':synthetic@', ':[YOUR-PASSWORD]@')
    $encoded = Resolve-PrivateConnection $placeholder 'Synthetic! @:/#'
    $checks.placeholder_password_escaped = ($encoded -ceq $placeholder.Replace('[YOUR-PASSWORD]',[Uri]::EscapeDataString('Synthetic! @:/#')))
    $checks.encoded_matching_duplicate_accepted = ((Resolve-PrivateConnection $encoded 'Synthetic! @:/#') -ceq $encoded)
    $cases = @(
        @{name='conflicting_passwords'; url=$urlValue; password='different'; stage='VALIDATING_DATABASE_PASSWORD'; error='DATABASE_PASSWORD_CONFLICT'},
        @{name='missing_password'; url=$placeholder; password=''; stage='VALIDATING_DATABASE_PASSWORD'; error='DATABASE_PASSWORD_REQUIRED'},
        @{name='wrong_pooler_project'; url=$urlValue.Replace('rpkjmdrralzxhdsgceal','otherproject'); password=''; stage='VALIDATING_PROJECT'; error='STAGING_PROJECT_MISMATCH'},
        @{name='wrong_direct_project'; url='postgresql://postgres:synthetic@db.otherproject.supabase.co:5432/postgres'; password=''; stage='VALIDATING_PROJECT'; error='STAGING_PROJECT_MISMATCH'},
        @{name='spoofed_pooler_host'; url=$urlValue.Replace('.pooler.supabase.com','.pooler.supabase.com.attacker.invalid'); password=''; stage='VALIDATING_PROJECT'; error='STAGING_PROJECT_MISMATCH'},
        @{name='transaction_pooler'; url=$urlValue.Replace(':5432/',':6543/'); password=''; stage='VALIDATING_ENDPOINT'; error='INVALID_STAGING_ENDPOINT'},
        @{name='query_target_override'; url=($urlValue+'?host=otherproject.invalid'); password=''; stage='VALIDATING_ENDPOINT'; error='UNSUPPORTED_CONNECTION_OPTION'}
    )
    foreach ($case in $cases) {
        $caught = $false
        try { $ignoredOutput = Resolve-PrivateConnection $case.url $case.password } catch {
            $caught = $true
            Write-InputStatus 'SAVE_FAILED' (Get-InputErrorType $_.Exception)
        }
        $safeStatus = Get-Content -LiteralPath ($target+'.status.json') -Raw | ConvertFrom-Json
        $checks[$case.name+'_specific_diagnostic'] = ($caught -and $safeStatus.failure_stage -ceq $case.stage -and $safeStatus.error_type -ceq $case.error)
    }
    $checks.validation_does_not_change_saved_file = ($before -ceq (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)
    if (@($checks.Values | Where-Object { $_ -ne $true }).Count -ne 0) { throw 'Private setup guard test failed.' }
    @{synthetic_private_input_guards='PASS'; checks=$checks} | ConvertTo-Json -Depth 3 -Compress
} finally {
    # Only this invocation's GUID-named synthetic files; never any owner setup.
    foreach ($file in @($target,$corrupt,($target+'.receipt.json'),($target+'.status.json'))) {
        if ([IO.File]::Exists($file)) { [IO.File]::Delete($file) }
    }
}
