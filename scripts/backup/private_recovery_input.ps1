# Private interactive input only. Credentials are protected by Windows DPAPI, never printed.
param([Parameter(Mandatory)][string]$Destination)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Security
$form = New-Object Windows.Forms.Form
$form.Text = 'Second Brain — private staging recovery setup'
$form.Size = New-Object Drawing.Size(680, 350)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$instructions = New-Object Windows.Forms.Label
$instructions.Text = 'Enter the STAGING session-pooler database URL for rpkjmdrralzxhdsgceal.' + "`n" + 'Choose a backup passphrase (20+ characters) and save it outside Google Drive.' + "`n" + 'Inputs stay local, encrypted for this Windows account. Do not send them in chat.'
$instructions.SetBounds(15, 15, 640, 65)
$url = New-Object Windows.Forms.TextBox
$url.UseSystemPasswordChar = $true
$url.SetBounds(15, 90, 630, 28)
$phraseLabel = New-Object Windows.Forms.Label
$phraseLabel.Text = 'Backup passphrase (save in your password manager)'
$phraseLabel.SetBounds(15, 130, 620, 22)
$phrase = New-Object Windows.Forms.TextBox
$phrase.UseSystemPasswordChar = $true
$phrase.SetBounds(15, 155, 630, 28)
$confirmLabel = New-Object Windows.Forms.Label
$confirmLabel.Text = 'Confirm backup passphrase'
$confirmLabel.SetBounds(15, 190, 620, 22)
$confirm = New-Object Windows.Forms.TextBox
$confirm.UseSystemPasswordChar = $true
$confirm.SetBounds(15, 215, 630, 28)
$button = New-Object Windows.Forms.Button
$button.Text = 'Save private setup'
$button.SetBounds(430, 260, 210, 35)
$button.Add_Click({
    try {
        $uri = [Uri]$url.Text.Trim()
        if ($uri.Scheme -notin @('postgres', 'postgresql') -or
            ($uri.Host -ne 'db.rpkjmdrralzxhdsgceal.supabase.co' -and
             -not ($uri.Host.EndsWith('.pooler.supabase.com') -and $uri.UserInfo.StartsWith('postgres.rpkjmdrralzxhdsgceal:')))) {
            throw 'Use only the staging project database URL.'
        }
        if ($uri.AbsolutePath -ne '/postgres' -or $uri.Port -eq 6543) { throw 'Use the session pooler on port 5432, database postgres.' }
        if ($phrase.Text.Length -lt 20 -or $phrase.Text -ne $confirm.Text) { throw 'Passphrases must match and contain at least 20 characters.' }
        $bytes = [Text.Encoding]::UTF8.GetBytes((@{database_url=$url.Text.Trim(); passphrase=$phrase.Text} | ConvertTo-Json -Compress))
        $protected = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        $parent = Split-Path -Parent $Destination
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        [IO.File]::WriteAllBytes($Destination, $protected)
        & icacls.exe $Destination /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(F)" | Out-Null
        [Array]::Clear($bytes, 0, $bytes.Length)
        $url.Clear(); $phrase.Clear(); $confirm.Clear()
        $form.DialogResult = [Windows.Forms.DialogResult]::OK
        $form.Close()
    } catch {
        [Windows.Forms.MessageBox]::Show('Check the staging URL and matching passphrases. Nothing was sent or printed.', 'Private setup') | Out-Null
    }
})
$form.Controls.AddRange(@($instructions, $url, $phraseLabel, $phrase, $confirmLabel, $confirm, $button))
$form.AcceptButton = $button
[void]$form.ShowDialog()
$form.Dispose()
