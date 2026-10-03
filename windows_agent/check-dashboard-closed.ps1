param([string]$ProcessName = "PCPowerSetup")

$ErrorActionPreference = "Stop"
if (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) {
    exit 1
}
exit 0
