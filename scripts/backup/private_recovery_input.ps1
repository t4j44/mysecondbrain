# Private interactive input only. Credentials are protected by Windows DPAPI, never printed.
param([string]$Destination, [switch]$SelfTest)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Security
if (-not $Destination) {
    $Destination = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'secure/SecondBrainRecovery/staging.dpapi'
}
$Destination = [IO.Path]::GetFullPath($Destination)

function Save-PrivateSetup([string]$DatabaseUrl, [string]$Passphrase, [string]$Target) {
    $bytes = $null
    $checked = $null
    $temporary = $null
    try {
        $payload = @{database_url=$DatabaseUrl; passphrase=$Passphrase; format_version=1}
        $bytes = [Text.Encoding]::UTF8.GetBytes(($payload | ConvertTo-Json -Compress))
        $protected = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $parent = Split-Path -Parent $Target
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        & icacls.exe $parent /inheritance:r /grant:r "$($identity.Name):(OI)(CI)F" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Private directory permissions failed.' }
        $temporary = Join-Path $parent ([IO.Path]::GetRandomFileName() + '.dpapi.partial')
        [IO.File]::WriteAllBytes($temporary, $protected)
        $checked = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($temporary), $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $verified = [Text.Encoding]::UTF8.GetString($checked) | ConvertFrom-Json
        if ($verified.database_url -cne $DatabaseUrl -or $verified.passphrase -cne $Passphrase) { throw 'Private read-back failed.' }
        # Atomic move refuses to overwrite a previously saved setup.
        [IO.File]::Move($temporary, $Target)
        $receipt = @{
            status='SAVED_AND_READ_BACK'; file=$Target; computer=$env:COMPUTERNAME
            account_sid=$identity.User.Value; session_id=[Diagnostics.Process]::GetCurrentProcess().SessionId
            saved_at=[DateTime]::UtcNow.ToString('o'); format_version=1
        }
        [IO.File]::WriteAllText(($Target + '.receipt.json'), ($receipt | ConvertTo-Json -Compress))
    } finally {
        if ($bytes) { [Array]::Clear($bytes, 0, $bytes.Length) }
        if ($checked) { [Array]::Clear($checked, 0, $checked.Length) }
        if ($temporary -and [IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
    }
}

if ($SelfTest) {
    $testTarget = Join-Path ([IO.Path]::GetTempPath()) ('sb-recovery-selftest-' + [Guid]::NewGuid().ToString('N') + '/synthetic.dpapi')
    try {
        Save-PrivateSetup 'postgresql://synthetic:synthetic@localhost/postgres' 'Synthetic self-test phrase only' $testTarget
        $status = Get-Content -LiteralPath ($testTarget + '.receipt.json') -Raw | ConvertFrom-Json
        if ($status.status -ne 'SAVED_AND_READ_BACK') { throw 'Self-test receipt failed.' }
        Write-Output 'Private form DPAPI write/read-back self-test PASS (synthetic inputs only).'
    } finally {
        # These two files are created exclusively by this synthetic self-test.
        if ([IO.File]::Exists($testTarget)) { [IO.File]::Delete($testTarget) }
        if ([IO.File]::Exists($testTarget + '.receipt.json')) { [IO.File]::Delete($testTarget + '.receipt.json') }
        if ([IO.Directory]::Exists([IO.Path]::GetDirectoryName($testTarget))) { [IO.Directory]::Delete([IO.Path]::GetDirectoryName($testTarget)) }
    }
    exit
}
$form = New-Object Windows.Forms.Form
$form.Text = 'Second Brain STAGING - verified private setup v2'
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
        Save-PrivateSetup $connectionUrl $phrase.Text $Destination
        $url.Clear(); $databasePassword.Clear(); $phrase.Clear(); $confirm.Clear()
        [Windows.Forms.MessageBox]::Show("Saved and verified for this Windows account.`n`n$Destination`n`nKeep your backup passphrase outside Google Drive. Codex will continue automatically.", 'Private recovery setup saved') | Out-Null
        $form.DialogResult = [Windows.Forms.DialogResult]::OK
        $form.Close()
    } catch {
        [Windows.Forms.MessageBox]::Show("The setup was not confirmed saved. Check the staging URL and matching passphrases, then retry. A previously saved setup will not be overwritten.`n`nDestination: $Destination", 'Private setup') | Out-Null
    }
})
$form.Controls.AddRange(@($instructions, $url, $databasePasswordLabel, $databasePassword, $phraseLabel, $phrase, $confirmLabel, $confirm, $button))
$form.AcceptButton = $button
[void]$form.ShowDialog()
$form.Dispose()
