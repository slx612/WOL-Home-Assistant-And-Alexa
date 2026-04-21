param(
    [string]$PythonLauncher = "py",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $agentDir "build"
$distDir = Join-Path $agentDir "dist"

if ($Clean) {
    Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $distDir -Recurse -Force -ErrorAction SilentlyContinue
}

& $PythonLauncher -m pip install --upgrade pyinstaller zeroconf pillow pystray

Push-Location $agentDir
try {
    & $PythonLauncher -m PyInstaller --noconfirm --clean --onefile --name PCPowerAgent pc_power_agent.py
    & $PythonLauncher -m PyInstaller --noconfirm --clean --onefile --windowed --name PCPowerTray --hidden-import pystray._win32 pc_power_tray.py
    & $PythonLauncher -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin --name PCPowerSetup setup_wizard_gui.py

    Copy-Item .\config.example.json (Join-Path $distDir "config.example.json") -Force
    Copy-Item .\install-task.ps1 (Join-Path $distDir "install-task.ps1") -Force
    Copy-Item .\uninstall-task.ps1 (Join-Path $distDir "uninstall-task.ps1") -Force
    Copy-Item .\add-firewall-rule.ps1 (Join-Path $distDir "add-firewall-rule.ps1") -Force

    Write-Host ""
    Write-Host "Compilacion completada." -ForegroundColor Green
    Write-Host "Agent:  $(Join-Path $distDir 'PCPowerAgent.exe')" -ForegroundColor Green
    Write-Host "Tray:   $(Join-Path $distDir 'PCPowerTray.exe')" -ForegroundColor Green
    Write-Host "Setup:  $(Join-Path $distDir 'PCPowerSetup.exe')" -ForegroundColor Green
    Write-Host ""
}
finally {
    Pop-Location
}
