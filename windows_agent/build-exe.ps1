param(
    [string]$PythonLauncher = "py",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $agentDir
$buildDir = Join-Path $agentDir "build"
$distDir = Join-Path $agentDir "dist"

function Invoke-PythonCommand {
    param(
        [string[]]$Arguments,
        [string]$StepName
    )

    & $PythonLauncher @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$StepName fallo con codigo $LASTEXITCODE"
    }
}

if ($Clean) {
    Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $distDir -Recurse -Force -ErrorAction SilentlyContinue
}

Invoke-PythonCommand -StepName "La instalacion de dependencias de build" -Arguments @(
    "-m",
    "pip",
    "install",
    "-r",
    (Join-Path $agentDir "requirements-build.txt")
)

Invoke-PythonCommand -StepName "WakeLink assets" -Arguments @((Join-Path $agentDir "build_assets.py"))

Push-Location $agentDir
try {
    $sharedPyInstallerArgs = @(
        "--noconfirm",
        "--clean",
        "--onefile",
        "--noupx",
        "--icon",
        (Join-Path $agentDir "assets\wakelink.ico"),
        "--paths",
        $projectRoot,
        "--hidden-import",
        "agent_core.common"
    )

    $agentBuildArgs = (
        "-m",
        "PyInstaller"
    ) + $sharedPyInstallerArgs + @(
        "--name",
        "PCPowerAgent",
        "--version-file",
        "assets\PCPowerAgent.version.txt",
        "pc_power_agent.py"
    )
    Invoke-PythonCommand -StepName "La compilacion de PCPowerAgent" -Arguments $agentBuildArgs

    $trayBuildArgs = (
        "-m",
        "PyInstaller"
    ) + $sharedPyInstallerArgs + @(
        "--windowed",
        "--name",
        "PCPowerTray",
        "--version-file",
        "assets\PCPowerTray.version.txt",
        "--hidden-import",
        "pystray._win32",
        "pc_power_tray.py"
    )
    Invoke-PythonCommand -StepName "La compilacion de PCPowerTray" -Arguments $trayBuildArgs

    $setupBuildArgs = (
        "-m",
        "PyInstaller"
    ) + $sharedPyInstallerArgs + @(
        "--windowed",
        "--version-file",
        "assets\PCPowerSetup.version.txt",
        "--add-data",
        "assets/wakelink.ico;assets",
        "--add-data",
        "install-task.ps1;.",
        "--name",
        "PCPowerSetup",
        "setup_wizard_gui.py"
    )
    Invoke-PythonCommand -StepName "La compilacion de PCPowerSetup" -Arguments $setupBuildArgs

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
