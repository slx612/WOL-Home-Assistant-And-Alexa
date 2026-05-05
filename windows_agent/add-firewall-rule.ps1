param(
    [string]$RuleName = "PC Power Agent",
    [int]$Port = 58477,
    [string[]]$RemoteAddresses
)

$ErrorActionPreference = "Stop"

if (-not $RemoteAddresses -or $RemoteAddresses.Count -eq 0) {
    throw "Debes indicar al menos una IP o rango en -RemoteAddresses"
}

if (Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue) {
    Remove-NetFirewallRule -DisplayName $RuleName
}

New-NetFirewallRule `
    -DisplayName $RuleName `
    -Direction Inbound `
    -Action Allow `
    -Enabled True `
    -Protocol TCP `
    -LocalPort $Port `
    -RemoteAddress ($RemoteAddresses -join ",") | Out-Null

Write-Host "Regla creada: $RuleName"
