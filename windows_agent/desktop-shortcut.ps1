param(
    [Parameter(Mandatory = $true)][string]$DesktopPath,
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [switch]$Create
)

$ErrorActionPreference = 'Stop'
$target = [IO.Path]::GetFullPath((Join-Path $InstallDir 'PCPowerSetup.exe'))
$shell = New-Object -ComObject WScript.Shell

foreach ($name in @('PC Power Free.lnk', 'WakeLink.lnk')) {
    $path = Join-Path $DesktopPath $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    $shortcut = $shell.CreateShortcut($path)
    if ($shortcut.TargetPath -and [string]::Equals(
        [IO.Path]::GetFullPath($shortcut.TargetPath), $target,
        [StringComparison]::OrdinalIgnoreCase
    )) {
        Remove-Item -LiteralPath $path -Force
    }
}

if ($Create) {
    $path = Join-Path $DesktopPath 'WakeLink.lnk'
    if (-not (Test-Path -LiteralPath $path)) {
        $shortcut = $shell.CreateShortcut($path)
        $shortcut.TargetPath = $target
        $shortcut.WorkingDirectory = $InstallDir
        $shortcut.Description = 'Open WakeLink'
        $shortcut.Save()
    }
}
