# Private interactive input only. Credentials are protected by Windows DPAPI, never printed.
param([string]$Destination, [switch]$SelfTest, [switch]$SelfTestClick, [switch]$KeepSynthetic, [switch]$LoadFunctionsOnly)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Security
$privateFolder = [IO.Path]::GetFullPath((Join-Path ([Environment]::GetFolderPath('UserProfile')) 'secure/SecondBrainRecovery'))
if (-not $Destination) {
    $Destination = Join-Path $privateFolder 'staging.dpapi'
    if ($SelfTest -or $SelfTestClick) { $Destination = Join-Path $privateFolder ('synthetic-validation-' + [Guid]::NewGuid().ToString('N') + '.dpapi') }
}
$Destination = [IO.Path]::GetFullPath($Destination)
if (-not [String]::Equals([IO.Path]::GetDirectoryName($Destination), $privateFolder, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Private setup must stay in the private Windows folder outside Git/worktrees.'
}
if ([IO.File]::Exists($Destination)) { throw 'An existing setup will not be overwritten.' }
if ($KeepSynthetic -and -not ($SelfTest -or $SelfTestClick)) { throw 'KeepSynthetic is a test-only option.' }
$script:RecoveryDestination = $Destination

function Set-PrivateDirectory([string]$Folder) {
    New-Item -ItemType Directory -Force -Path $Folder | Out-Null
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    # icacls changes the DACL only; Set-Acl with a new descriptor can request
    # SeSecurityPrivilege for audit/owner fields even on an owner-controlled folder.
    & icacls.exe $Folder /inheritance:r /grant:r "*$($sid.Value):(OI)(CI)F" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Private directory permissions failed.' }
    $acl = Get-Acl -LiteralPath $Folder
    foreach ($principal in @($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | ForEach-Object { $_.IdentityReference.Value } | Select-Object -Unique)) {
        if ($principal -ne $sid.Value) {
            & icacls.exe $Folder /remove "*$principal" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Unexpected directory access could not be removed.' }
        }
    }
}

function Assert-PrivateFile([string]$Target, [string]$DatabaseUrl, [string]$Passphrase) {
    if (-not [IO.File]::Exists($Target)) { throw 'Final private setup file is missing.' }
    $protected = [IO.File]::ReadAllBytes($Target)
    $checked = $null
    try {
        $checked = [Security.Cryptography.ProtectedData]::Unprotect($protected, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $verified = [Text.Encoding]::UTF8.GetString($checked) | ConvertFrom-Json
        if ($verified.database_url -cne $DatabaseUrl -or $verified.passphrase -cne $Passphrase) { throw 'Final private file read-back failed.' }
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        $acl = Get-Acl -LiteralPath $Target
        $rules = @($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
        if ($rules.Count -lt 1) { throw 'Private file has no restrictive access rules.' }
        foreach ($access in $rules) {
            if ($access.IdentityReference.Value -ne $sid -or $access.AccessControlType -ne 'Allow') {
                throw 'Unexpected private file permissions.'
            }
        }
        $hash = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
        return @{file_exists=$true; final_read_back='PASS'; private_permissions='PASS'; bytes=$protected.Length; sha256=$hash}
    } finally {
        if ($checked) { [Array]::Clear($checked, 0, $checked.Length) }
    }
}

function Write-InputStatus([string]$Status, [string]$ErrorType='') {
    $target = $script:RecoveryDestination
    $parent = Split-Path -Parent $target
    Set-PrivateDirectory $parent
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $metadata = @{status=$Status; file=$target; error_type=$ErrorType; account_sid=$identity.User.Value
        session_id=[Diagnostics.Process]::GetCurrentProcess().SessionId; process_id=$PID; computer=$env:COMPUTERNAME
        updated_at=[DateTime]::UtcNow.ToString('o')}
    [IO.File]::WriteAllText(($target + '.status.json'), ($metadata | ConvertTo-Json -Compress))
}

function Save-PrivateSetup([string]$DatabaseUrl, [string]$Passphrase, [string]$Target) {
    $bytes = $null
    $checked = $null
    $temporary = $null
    try {
        $payload = @{database_url=$DatabaseUrl; passphrase=$Passphrase; format_version=1; synthetic_test=[bool]($SelfTest -or $SelfTestClick)}
        $bytes = [Text.Encoding]::UTF8.GetBytes(($payload | ConvertTo-Json -Compress))
        $protected = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $parent = Split-Path -Parent $Target
        Set-PrivateDirectory $parent
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $temporary = Join-Path $parent ([IO.Path]::GetRandomFileName() + '.dpapi.partial')
        $stream = New-Object IO.FileStream($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None, 4096, [IO.FileOptions]::WriteThrough)
        try { $stream.Write($protected, 0, $protected.Length); $stream.Flush($true) } finally { $stream.Dispose() }
        $checked = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($temporary), $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $verified = [Text.Encoding]::UTF8.GetString($checked) | ConvertFrom-Json
        if ($verified.database_url -cne $DatabaseUrl -or $verified.passphrase -cne $Passphrase) { throw 'Private read-back failed.' }
        # Atomic move refuses to overwrite a previously saved setup.
        [IO.File]::Move($temporary, $Target)
        $proof = Assert-PrivateFile $Target $DatabaseUrl $Passphrase
        $receipt = @{
            status='SAVED_AND_READ_BACK'; file=$Target; computer=$env:COMPUTERNAME
            account_sid=$identity.User.Value; session_id=[Diagnostics.Process]::GetCurrentProcess().SessionId
            saved_at=[DateTime]::UtcNow.ToString('o'); format_version=1
            final_read_back=$proof.final_read_back; private_permissions=$proof.private_permissions
            sha256=$proof.sha256; bytes=$proof.bytes; synthetic_test=[bool]($SelfTest -or $SelfTestClick)
        }
        [IO.File]::WriteAllText(($Target + '.receipt.json'), ($receipt | ConvertTo-Json -Compress))
    } finally {
        if ($bytes) { [Array]::Clear($bytes, 0, $bytes.Length) }
        if ($checked) { [Array]::Clear($checked, 0, $checked.Length) }
        if ($temporary -and [IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}

if ($LoadFunctionsOnly) { return }

if ($SelfTest) {
    $testTarget = $Destination
    try {
        Save-PrivateSetup 'postgresql://synthetic:synthetic@localhost/postgres' 'Synthetic self-test phrase only' $testTarget
        $status = Get-Content -LiteralPath ($testTarget + '.receipt.json') -Raw | ConvertFrom-Json
        if ($status.status -ne 'SAVED_AND_READ_BACK') { throw 'Self-test receipt failed.' }
        Write-Output 'Private form DPAPI write/read-back self-test PASS (synthetic inputs only).'
    } finally {
        # These two files are created exclusively by this synthetic self-test.
        if ([IO.File]::Exists($testTarget)) { [IO.File]::Delete($testTarget) }
        if ([IO.File]::Exists($testTarget + '.receipt.json')) { [IO.File]::Delete($testTarget + '.receipt.json') }
    }
    exit
}
$form = New-Object Windows.Forms.Form
$form.Text = 'Second Brain STAGING - verified private setup v4'
$form.Size = New-Object Drawing.Size(680, 430)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$instructions = New-Object Windows.Forms.Label
$instructions.Text = 'STAGING ONLY: second-brain-staging (rpkjmdrralzxhdsgceal), session-pooler URL.' + "`n" + 'Choose a backup passphrase (20+ characters) and save it outside Google Drive.' + "`n" + 'Saved outside Git/worktrees in your private Windows folder. Never send inputs in chat.'
$instructions.SetBounds(15, 15, 640, 65)
$url = New-Object Windows.Forms.TextBox
$url.UseSystemPasswordChar = $true
$url.SetBounds(15, 90, 630, 28)
$databasePasswordLabel = New-Object Windows.Forms.Label
$databasePasswordLabel.Text = 'Staging database password (only if the URL contains [YOUR-PASSWORD])'
$databasePasswordLabel.SetBounds(15, 130, 630, 22)
$databasePassword = New-Object Windows.Forms.TextBox
$databasePassword.UseSystemPasswordChar = $true
$databasePassword.SetBounds(15, 155, 630, 28)
$phraseLabel = New-Object Windows.Forms.Label
$phraseLabel.Text = 'Backup passphrase (save in your password manager)'
$phraseLabel.SetBounds(15, 205, 620, 22)
$phrase = New-Object Windows.Forms.TextBox
$phrase.UseSystemPasswordChar = $true
$phrase.SetBounds(15, 230, 630, 28)
$confirmLabel = New-Object Windows.Forms.Label
$confirmLabel.Text = 'Confirm backup passphrase'
$confirmLabel.SetBounds(15, 265, 620, 22)
$confirm = New-Object Windows.Forms.TextBox
$confirm.UseSystemPasswordChar = $true
$confirm.SetBounds(15, 290, 630, 28)
$button = New-Object Windows.Forms.Button
$button.Text = 'Save private setup'
$button.SetBounds(430, 335, 210, 35)
$button.Add_Click({
    try {
        Write-InputStatus 'SAVE_CLICK_RECEIVED'
        $connectionUrl = $url.Text.Trim()
        if ($connectionUrl.Contains('[YOUR-PASSWORD]')) {
            if (-not $databasePassword.Text) { throw 'Enter the staging database password in its separate masked field.' }
            $connectionUrl = $connectionUrl.Replace('[YOUR-PASSWORD]', [Uri]::EscapeDataString($databasePassword.Text))
        } elseif ($databasePassword.Text) {
            throw 'For a URL already containing its password, leave the separate database password field empty.'
        }
        $uri = [Uri]$connectionUrl
        if ($uri.Scheme -notin @('postgres', 'postgresql') -or
            ($uri.Host -ne 'db.rpkjmdrralzxhdsgceal.supabase.co' -and
             -not ($uri.Host.EndsWith('.pooler.supabase.com') -and $uri.UserInfo.StartsWith('postgres.rpkjmdrralzxhdsgceal:')))) {
            throw 'Use only the staging project database URL.'
        }
        if ($uri.AbsolutePath -ne '/postgres' -or $uri.Port -notin @(-1,5432) -or $uri.UserInfo -notmatch ':.+') { throw 'Use the session pooler on port 5432, database postgres.' }
        if ($phrase.Text.Length -lt 20 -or $phrase.Text -ne $confirm.Text) { throw 'Passphrases must match and contain at least 20 characters.' }
        Write-InputStatus 'WRITING_ENCRYPTED_FILE'
        if ([IO.File]::Exists($script:RecoveryDestination)) {
            # A reader failure after the atomic save must allow verification to
            # be retried with the existing masked values, without overwriting.
            Assert-PrivateFile $script:RecoveryDestination $connectionUrl $phrase.Text | Out-Null
        } else {
            Save-PrivateSetup $connectionUrl $phrase.Text $script:RecoveryDestination
        }
        Write-InputStatus 'VERIFYING_WITH_BACKUP_READER'
        $python = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../apps/api/.venv/Scripts/python.exe'))
        $verifier = Join-Path $PSScriptRoot 'verify_private_setup.py'
        $arguments = @($verifier, '--path', $script:RecoveryDestination)
        if ($SelfTestClick) { $arguments += '--allow-synthetic' }
        $readerOutput = & $python @arguments 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Independent backup reader verification failed.' }
        $readerProof = $readerOutput | ConvertFrom-Json
        if ($readerProof.windows_decryption -ne 'PASS' -or -not $readerProof.file_exists) { throw 'Independent backup reader verification failed.' }
        $receiptPath = $script:RecoveryDestination + '.receipt.json'
        $receipt = [IO.File]::ReadAllText($receiptPath) | ConvertFrom-Json
        if ($receipt.sha256 -cne $readerProof.sha256) { throw 'Independent final-file checksum mismatch.' }
        $receipt | Add-Member -NotePropertyName backup_reader -NotePropertyValue 'PASS'
        [IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Compress))
        if (-not [IO.File]::Exists($script:RecoveryDestination)) { throw 'Final file disappeared before success.' }
        Write-InputStatus 'SAVED_AND_VERIFIED'
        $url.Clear(); $databasePassword.Clear(); $phrase.Clear(); $confirm.Clear()
        if (-not $SelfTestClick) {
            [Windows.Forms.MessageBox]::Show("Saved and verified for this Windows account.`n`n$Destination`n`nKeep your backup passphrase outside Google Drive. Codex will continue automatically.", 'Private recovery setup saved') | Out-Null
        }
        $form.DialogResult = [Windows.Forms.DialogResult]::OK
        $form.Close()
    } catch {
        Write-InputStatus 'SAVE_FAILED' $_.Exception.GetType().Name
        if ($SelfTestClick) { $form.Close() } else {
            [Windows.Forms.MessageBox]::Show("Save or verification failed. No success was recorded. Your masked inputs remain in this form; leave it open so the private status can be diagnosed. An existing file will not be overwritten.`n`nDestination: $Destination", 'Private setup verification failed') | Out-Null
        }
    }
})
$form.Controls.AddRange(@($instructions, $url, $databasePasswordLabel, $databasePassword, $phraseLabel, $phrase, $confirmLabel, $confirm, $button))
$form.AcceptButton = $button
Write-InputStatus 'FORM_OPEN'
if ($SelfTestClick) {
    $url.Text = 'postgresql://postgres.rpkjmdrralzxhdsgceal:[YOUR-PASSWORD]@aws-0-synthetic.pooler.supabase.com:5432/postgres'
    $databasePassword.Text = 'Synthetic test only! @:/#'
    $phrase.Text = 'Synthetic click test phrase only'
    $confirm.Text = $phrase.Text
    $form.Add_Shown({ $button.PerformClick() })
}
[void]$form.ShowDialog()
$form.Dispose()
if ($SelfTestClick) {
    try {
        $status = Get-Content -LiteralPath ($Destination + '.status.json') -Raw | ConvertFrom-Json
        if ($status.status -ne 'SAVED_AND_VERIFIED' -or -not [IO.File]::Exists($Destination)) {
            throw ('Save-button flow failed: ' + $status.error_type)
        }
        Write-Output 'Private form save-button flow PASS (synthetic inputs only).'
    } finally {
        if (-not $KeepSynthetic) {
            foreach ($testFile in @($Destination, ($Destination + '.receipt.json'), ($Destination + '.status.json'))) {
                if ([IO.File]::Exists($testFile)) { [IO.File]::Delete($testFile) }
            }
        }
    }
}
