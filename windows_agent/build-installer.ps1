param(
    [switch]$Clean,
    [switch]$RebuildExe
)

$ErrorActionPreference = "Stop"

$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $agentDir "dist"
$installerScript = Join-Path $agentDir "pcpowerfree-installer.nsi"
$toolsDir = Join-Path $agentDir ".tools"
$portableNsisDir = Join-Path $toolsDir "nsis"
$portableNsisZip = Join-Path $toolsDir "nsis-3.11.zip"

if (
    $RebuildExe -or
    -not (Test-Path (Join-Path $distDir "PCPowerAgent.exe")) -or
    -not (Test-Path (Join-Path $distDir "PCPowerTray.exe")) -or
    -not (Test-Path (Join-Path $distDir "PCPowerSetup.exe"))
) {
    & (Join-Path $agentDir "build-exe.ps1") -Clean:$Clean
}

function Get-MakeNsisPath {
    $command = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in @(
        (Join-Path $env:ProgramFiles "NSIS\makensis.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "NSIS\Bin\makensis.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    $portableCandidate = Get-ChildItem -Path $portableNsisDir -Filter makensis.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($portableCandidate) {
        return $portableCandidate.FullName
    }

    return $null
}

function Install-PortableNsis {
    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
    $downloadUrl = "https://downloads.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $portableNsisZip

    if (Test-Path $portableNsisDir) {
        Remove-Item $portableNsisDir -Recurse -Force
    }

    Expand-Archive -LiteralPath $portableNsisZip -DestinationPath $portableNsisDir -Force
}

$makensisPath = Get-MakeNsisPath
if (-not $makensisPath) {
    try {
        winget install --id NSIS.NSIS --silent --accept-package-agreements --accept-source-agreements
    }
    catch {
        Write-Warning "No se pudo instalar NSIS con winget. Se intentara usar la version ZIP portable."
    }
    $makensisPath = Get-MakeNsisPath
}

if (-not $makensisPath) {
    Install-PortableNsis
    $makensisPath = Get-MakeNsisPath
}

if (-not $makensisPath) {
    throw "No se ha encontrado makensis.exe ni despues de descargar la version portable de NSIS."
}

$makensisPath = [string]$makensisPath

Push-Location $agentDir
try {
    & "$makensisPath" "/DOUTPUT_DIR=$distDir" "$installerScript"
    if ($LASTEXITCODE -ne 0) {
        throw "makensis.exe devolvio el codigo $LASTEXITCODE"
    }
    Write-Host ""
    Write-Host "Instalador generado:" -ForegroundColor Green
    Write-Host "$(Join-Path $distDir 'pcpowerfree-windows-x64-setup.exe')" -ForegroundColor Green
    Write-Host ""
}
finally {
    Pop-Location
}
