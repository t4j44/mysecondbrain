param([Parameter(Mandatory = $true)][string]$Path)
$ErrorActionPreference = 'Stop'
# A Python child launched by PowerShell 7 inherits its incompatible module path.
# Load the built-in module belonging to this Windows PowerShell executable.
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Security/Microsoft.PowerShell.Security.psd1') -Force
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
$system = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
if (-not (Test-Path -LiteralPath $Path)) {
    $directory = New-Item -ItemType Directory -Path $Path
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner($identity)
    $acl.SetAccessRuleProtection($true, $false)
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
        $identity, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $acl.AddAccessRule($rule)
    Set-Acl -LiteralPath $directory.FullName -AclObject $acl
}
$directory = Get-Item -LiteralPath $Path -Force
if (-not $directory.PSIsContainer -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Recovery work directory must be a real directory.'
}
$acl = Get-Acl -LiteralPath $directory.FullName
if (-not $acl.AreAccessRulesProtected -or $acl.GetOwner([Security.Principal.SecurityIdentifier]) -ne $identity) {
    throw 'Recovery work directory must be owned by this account with inheritance disabled.'
}
$ownerAccess = $false
foreach ($rule in $acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier])) {
    if ($rule.AccessControlType -ne 'Allow') { continue }
    if ($rule.IdentityReference -ne $identity -and $rule.IdentityReference -ne $system) {
        throw 'Recovery work directory permits another account. Use a new private directory.'
    }
    if ($rule.IdentityReference -eq $identity -and -not $rule.IsInherited -and
        ($rule.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -eq [Security.AccessControl.FileSystemRights]::FullControl -and
        ($rule.InheritanceFlags -band [Security.AccessControl.InheritanceFlags]::ContainerInherit) -and
        ($rule.InheritanceFlags -band [Security.AccessControl.InheritanceFlags]::ObjectInherit) -and
        $rule.PropagationFlags -eq [Security.AccessControl.PropagationFlags]::None) { $ownerAccess = $true }
}
if (-not $ownerAccess) { throw 'Recovery work directory lacks inheritable owner-only access.' }
