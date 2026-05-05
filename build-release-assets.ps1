param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseDir = Join-Path $repoRoot "release_assets"
$stageDir = Join-Path $releaseDir ".zip_stage"
$integrationSourceDir = Join-Path $repoRoot "custom_components\\pc_power_free"
$integrationStageDir = Join-Path $stageDir "custom_components\\pc_power_free"
$integrationZipPath = Join-Path $releaseDir "pcpowerfree-home-assistant-integration.zip"
$linuxBundlePath = Join-Path $releaseDir "pcpowerfree-linux-agent.tar.gz"

function Copy-DirectoryWithoutCaches {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDir,
        [Parameter(Mandatory = $true)]
        [string]$TargetDir
    )

    $sourceRoot = (Resolve-Path $SourceDir).Path
    foreach ($item in Get-ChildItem -Path $sourceRoot -Recurse -Force) {
        $relativePath = $item.FullName.Substring($sourceRoot.Length).TrimStart('\')
        if (-not $relativePath) {
            continue
        }

        if ($relativePath -match '(^|\\)__pycache__(\\|$)' -or $relativePath -match '\.pyc$') {
            continue
        }

        $destinationPath = Join-Path $TargetDir $relativePath
        if ($item.PSIsContainer) {
            New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
            continue
        }

        $destinationDir = Split-Path -Parent $destinationPath
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        Copy-Item -LiteralPath $item.FullName -Destination $destinationPath -Force
    }
}

if (Test-Path $stageDir) {
    Remove-Item -LiteralPath $stageDir -Recurse -Force
}

if (Test-Path $integrationZipPath) {
    Remove-Item -LiteralPath $integrationZipPath -Force
}

if (Test-Path $linuxBundlePath) {
    Remove-Item -LiteralPath $linuxBundlePath -Force
}

New-Item -ItemType Directory -Path $integrationStageDir -Force | Out-Null
Copy-DirectoryWithoutCaches -SourceDir $integrationSourceDir -TargetDir $integrationStageDir
Compress-Archive -Path (Join-Path $stageDir "custom_components") -DestinationPath $integrationZipPath -CompressionLevel Optimal

tar -czf $linuxBundlePath `
    --exclude='__pycache__' `
    --exclude='*.pyc' `
    -C $repoRoot `
    agent_core `
    linux_agent

if (Test-Path $stageDir) {
    Remove-Item -LiteralPath $stageDir -Recurse -Force
}

Write-Host ""
Write-Host "Release assets generated:" -ForegroundColor Green
Write-Host $integrationZipPath -ForegroundColor Green
Write-Host $linuxBundlePath -ForegroundColor Green
Write-Host ""
