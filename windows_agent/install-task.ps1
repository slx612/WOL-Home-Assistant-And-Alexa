param(
    [string]$TaskName = "PC Power Agent",
    [string]$PythonExe = "",
    [string]$ConfigPath = "",
    [string]$ExecutablePath = ""
)

$ErrorActionPreference = "Stop"

$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $agentDir "pc_power_agent.py"
$defaultExePath = Join-Path $agentDir "PCPowerAgent.exe"
$programDataDir = Join-Path $env:ProgramData "PC Power Free"
$programDataConfig = Join-Path $programDataDir "config.json"

function Test-IsInstalledLocation {
    param([string]$PathToCheck)

    $resolved = [System.IO.Path]::GetFullPath($PathToCheck)
    $programFiles = [System.IO.Path]::GetFullPath($env:ProgramFiles)
    $programFilesX86 = [System.IO.Path]::GetFullPath(${env:ProgramFiles(x86)})
    return $resolved.StartsWith($programFiles, [System.StringComparison]::OrdinalIgnoreCase) -or
        $resolved.StartsWith($programFilesX86, [System.StringComparison]::OrdinalIgnoreCase)
}

if (-not $ExecutablePath -and (Test-Path $defaultExePath)) {
    $ExecutablePath = $defaultExePath
}

if (-not $ExecutablePath) {
    if (-not $PythonExe) {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($pythonCommand) {
            $PythonExe = $pythonCommand.Source
        }
        else {
            $PythonExe = (Get-Command py.exe).Source
        }
    }
}

if (-not $ConfigPath) {
    if (Test-IsInstalledLocation -PathToCheck $agentDir) {
        $ConfigPath = $programDataConfig
    }
    else {
        $ConfigPath = Join-Path $agentDir "config.json"
    }
}

if (-not (Test-Path $ConfigPath)) {
    throw "No se encuentra $ConfigPath. Crea primero config.json a partir de config.example.json"
}

if (-not $ExecutablePath -and -not (Test-Path $scriptPath)) {
    throw "No se encuentra $scriptPath"
}

if ($ExecutablePath -and -not (Test-Path $ExecutablePath)) {
    throw "No se encuentra $ExecutablePath"
}

if ($ExecutablePath) {
    $action = New-ScheduledTaskAction -Execute $ExecutablePath -Argument "--config `"$ConfigPath`""
}
else {
    $pythonPrefix = ""
    if ([System.IO.Path]::GetFileName($PythonExe).ToLowerInvariant() -eq "py.exe") {
        $pythonPrefix = "-3 "
    }

    $action = New-ScheduledTaskAction -Execute $PythonExe -Argument "$pythonPrefix`"$scriptPath`" --config `"$ConfigPath`""
}
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host "Tarea instalada y arrancada: $TaskName"
