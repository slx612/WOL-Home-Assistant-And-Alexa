Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$buildRoot = Join-Path $scriptRoot "build"
$distRoot = Join-Path $scriptRoot "dist"
$templateRoot = Join-Path $scriptRoot "template"
$payloadRoot = Join-Path $scriptRoot "payload"
$dsmAsyncTimeoutVersion = "4.0.3"
$dsmIfaddrVersion = "0.2.0"
$dsmZeroconfVersion = "0.122.3"

function Get-AppVersion {
    $commonPath = Join-Path $projectRoot "agent_core\common.py"
    $match = [regex]::Match(
        (Get-Content -LiteralPath $commonPath -Raw),
        'AGENT_VERSION\s*=\s*"([^"]+)"'
    )
    if (-not $match.Success) {
        throw "Could not determine AGENT_VERSION from agent_core/common.py"
    }
    return $match.Groups[1].Value
}

function Convert-ToDsmPackageVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $match = [regex]::Match($Version, '^(?<base>\d+(?:\.\d+){1,3})(?:-beta\.(?<beta>\d+))?$')
    if (-not $match.Success) {
        throw "Unsupported version format for DSM package: $Version"
    }

    $baseVersion = $match.Groups["base"].Value
    $betaGroup = $match.Groups["beta"]
    if ($betaGroup.Success) {
        return "{0}-{1:0000}" -f $baseVersion, [int]$betaGroup.Value
    }

    return "$baseVersion-0000"
}

function Copy-FilteredTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    $resolvedSource = (Resolve-Path -LiteralPath $Source).Path
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    Get-ChildItem -LiteralPath $resolvedSource -Force -Recurse | ForEach-Object {
        $relativePath = $_.FullName.Substring($resolvedSource.Length).TrimStart('\')
        if (-not $relativePath) {
            return
        }

        if (
            $relativePath -match '(^|\\)(__pycache__|build|dist|\.venv)(\\|$)' -or
            $relativePath -match '\.pyc$'
        ) {
            return
        }

        $targetPath = Join-Path $Destination $relativePath
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $targetPath | Out-Null
            return
        }

        $targetParent = Split-Path -Parent $targetPath
        if ($targetParent) {
            New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        }
        Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Force
    }
}

function Install-VendoredDependencies {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DestinationRoot
    )

    Remove-Item -LiteralPath $DestinationRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null

    & py -3 -m pip install `
        --target $DestinationRoot `
        "async-timeout==$dsmAsyncTimeoutVersion" `
        "ifaddr==$dsmIfaddrVersion" `
        "zeroconf==$dsmZeroconfVersion"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install pinned DSM vendored dependencies into $DestinationRoot"
    }
}

function Copy-VendoredDependency {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SitePackagesRoot,
        [Parameter(Mandatory = $true)]
        [string]$PackageName,
        [Parameter(Mandatory = $true)]
        [string]$DestinationRoot
    )

    $sourceDir = Join-Path $SitePackagesRoot $PackageName
    if (-not (Test-Path -LiteralPath $sourceDir)) {
        throw "Missing vendored dependency source: $sourceDir"
    }

    $destinationDir = Join-Path $DestinationRoot $PackageName
    Copy-FilteredTree -Source $sourceDir -Destination $destinationDir

    Get-ChildItem -LiteralPath $destinationDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @(".pyd", ".so", ".dll", ".dylib", ".pyc", ".pyo") } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

function Write-ResizedPng {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination,
        [Parameter(Mandatory = $true)]
        [int]$Size
    )

    Add-Type -AssemblyName System.Drawing

    $image = [System.Drawing.Image]::FromFile($Source)
    try {
        $bitmap = New-Object System.Drawing.Bitmap $Size, $Size
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $graphics.Clear([System.Drawing.Color]::Transparent)
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.DrawImage($image, 0, 0, $Size, $Size)
            }
            finally {
                $graphics.Dispose()
            }

            $bitmap.Save($Destination, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $bitmap.Dispose()
        }
    }
    finally {
        $image.Dispose()
    }
}

$appVersion = Get-AppVersion
$dsmPackageVersion = Convert-ToDsmPackageVersion -Version $appVersion
$packageName = "pcpowerfree"
$packageFileName = "pcpowerfree-dsm-noarch-$dsmPackageVersion.spk"

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $distRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $buildRoot, $distRoot | Out-Null

$spkRoot = Join-Path $buildRoot "spk"
$payloadStage = Join-Path $buildRoot "payload"
New-Item -ItemType Directory -Force -Path $spkRoot, $payloadStage | Out-Null

Copy-Item -LiteralPath (Join-Path $templateRoot "conf") -Destination $spkRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $templateRoot "scripts") -Destination $spkRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination (Join-Path $spkRoot "LICENSE") -Force

$infoTemplate = Get-Content -LiteralPath (Join-Path $templateRoot "INFO.in") -Raw
$infoContent = $infoTemplate.Replace("@@APP_VERSION@@", $appVersion).Replace("@@DSM_PACKAGE_VERSION@@", $dsmPackageVersion)
[System.IO.File]::WriteAllText(
    (Join-Path $spkRoot "INFO"),
    $infoContent,
    (New-Object System.Text.UTF8Encoding($false))
)

$appStage = Join-Path $payloadStage "app"
New-Item -ItemType Directory -Force -Path $appStage | Out-Null
Copy-FilteredTree -Source (Join-Path $projectRoot "agent_core") -Destination (Join-Path $appStage "agent_core")
Copy-FilteredTree -Source (Join-Path $projectRoot "linux_agent") -Destination (Join-Path $appStage "linux_agent")
Copy-FilteredTree -Source (Join-Path $payloadRoot "dsm_runtime") -Destination (Join-Path $appStage "dsm_runtime")
Copy-Item -LiteralPath (Join-Path $payloadRoot "share") -Destination $appStage -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "linux_agent\config.example.json") -Destination (Join-Path $appStage "share\config.example.json") -Force
$vendorStage = Join-Path $appStage "vendor"
New-Item -ItemType Directory -Force -Path $vendorStage | Out-Null
$vendorSourceRoot = Join-Path $buildRoot "_vendor_source"
Install-VendoredDependencies -DestinationRoot $vendorSourceRoot
Copy-VendoredDependency -SitePackagesRoot $vendorSourceRoot -PackageName "ifaddr" -DestinationRoot $vendorStage
Copy-VendoredDependency -SitePackagesRoot $vendorSourceRoot -PackageName "async_timeout" -DestinationRoot $vendorStage
Copy-VendoredDependency -SitePackagesRoot $vendorSourceRoot -PackageName "zeroconf" -DestinationRoot $vendorStage
Remove-Item -LiteralPath (Join-Path $appStage "linux_agent\README.md") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $appStage "linux_agent\pcpowerfree-agent.service") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $appStage "linux_agent\config.example.json") -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Join-Path $payloadStage "var") | Out-Null

$iconSource = Join-Path $projectRoot "custom_components\pc_power_free\brand\icon.png"
Write-ResizedPng -Source $iconSource -Destination (Join-Path $spkRoot "PACKAGE_ICON.PNG") -Size 64
Copy-Item -LiteralPath $iconSource -Destination (Join-Path $spkRoot "PACKAGE_ICON_256.PNG") -Force

$packageTgz = Join-Path $buildRoot "package.tgz"
tar -czf $packageTgz -C $payloadStage .
Copy-Item -LiteralPath $packageTgz -Destination (Join-Path $spkRoot "package.tgz") -Force

$finalSpk = Join-Path $distRoot $packageFileName
& tar --format=ustar -cf $finalSpk -C $spkRoot `
    INFO `
    package.tgz `
    scripts `
    conf `
    LICENSE `
    PACKAGE_ICON.PNG `
    PACKAGE_ICON_256.PNG
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create DSM package archive: $finalSpk"
}

Write-Host "Built DSM package scaffold:"
Write-Host "  App version: $appVersion"
Write-Host "  DSM package version: $dsmPackageVersion"
Write-Host "  package.tgz: $packageTgz"
Write-Host "  SPK: $finalSpk"
