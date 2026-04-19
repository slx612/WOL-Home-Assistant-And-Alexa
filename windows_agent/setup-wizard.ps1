param(
    [string]$ConfigPath = "",
    [int]$AgentPort = 8777,
    [string]$TaskName = "PC Power Agent"
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Convert-IPv4ToUInt32 {
    param([string]$IpAddress)

    $bytes = [System.Net.IPAddress]::Parse($IpAddress).GetAddressBytes()
    [Array]::Reverse($bytes)
    return [BitConverter]::ToUInt32($bytes, 0)
}

function Convert-UInt32ToIPv4 {
    param([uint32]$Value)

    $bytes = [BitConverter]::GetBytes($Value)
    [Array]::Reverse($bytes)
    return ([System.Net.IPAddress]::new($bytes)).ToString()
}

function Get-IPv4NetworkCidr {
    param(
        [string]$IpAddress,
        [int]$PrefixLength
    )

    [uint32]$ipValue = Convert-IPv4ToUInt32 -IpAddress $IpAddress
    [uint32]$maskValue = if ($PrefixLength -eq 0) { 0 } else { [uint32]::MaxValue -shl (32 - $PrefixLength) }
    [uint32]$networkValue = $ipValue -band $maskValue
    $networkAddress = Convert-UInt32ToIPv4 -Value $networkValue
    return "$networkAddress/$PrefixLength"
}

function Get-DirectedBroadcast {
    param(
        [string]$IpAddress,
        [int]$PrefixLength
    )

    [uint32]$ipValue = Convert-IPv4ToUInt32 -IpAddress $IpAddress
    [uint32]$maskValue = if ($PrefixLength -eq 0) { 0 } else { [uint32]::MaxValue -shl (32 - $PrefixLength) }
    [uint32]$broadcastValue = ($ipValue -band $maskValue) -bor (-bnot $maskValue)
    return Convert-UInt32ToIPv4 -Value $broadcastValue
}

function New-RandomToken {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd("=") -replace "\+", "-" -replace "/", "_"
}

function New-PairingCode {
    return (Get-Random -Minimum 100000 -Maximum 1000000).ToString()
}

function Get-Sha256Hex {
    param([string]$Value)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $hashBytes = $sha.ComputeHash($bytes)
        return ([BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-PrimaryAdapterInfo {
    $candidates = Get-NetIPConfiguration | Where-Object {
        $_.NetAdapter.Status -eq "Up" -and
        $_.IPv4Address -and
        $_.NetAdapter.HardwareInterface
    }

    if (-not $candidates) {
        throw "No se ha encontrado un adaptador de red IPv4 activo."
    }

    $selected = $candidates | Select-Object -First 1
    $ipAddress = $selected.IPv4Address.IPAddress
    $prefixLength = [int]$selected.IPv4Address.PrefixLength
    $macAddress = ($selected.NetAdapter.MacAddress -replace "-", ":").ToUpperInvariant()
    $subnetCidr = Get-IPv4NetworkCidr -IpAddress $ipAddress -PrefixLength $prefixLength
    $broadcastAddress = Get-DirectedBroadcast -IpAddress $ipAddress -PrefixLength $prefixLength

    return [PSCustomObject]@{
        InterfaceAlias   = $selected.InterfaceAlias
        IPv4Address      = $ipAddress
        PrefixLength     = $prefixLength
        MacAddress       = $macAddress
        SubnetCidr       = $subnetCidr
        BroadcastAddress = $broadcastAddress
        Hostname         = $env:COMPUTERNAME
    }
}

function Read-DefaultValue {
    param(
        [string]$Prompt,
        [string]$DefaultValue = ""
    )

    if ($DefaultValue) {
        $value = Read-Host "$Prompt [$DefaultValue]"
        if ([string]::IsNullOrWhiteSpace($value)) {
            return $DefaultValue
        }
        return $value.Trim()
    }

    return (Read-Host $Prompt).Trim()
}

$agentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ConfigPath) {
    $ConfigPath = Join-Path $agentDir "config.json"
}

$adapter = Get-PrimaryAdapterInfo
$token = New-RandomToken
$pairingCode = New-PairingCode
$machineId = [guid]::NewGuid().ToString("N")
$isAdmin = Test-IsAdministrator

Write-Host ""
Write-Host "PC Power Free - Asistente de instalacion" -ForegroundColor Cyan
Write-Host ""
Write-Host "Datos detectados automaticamente:" -ForegroundColor Yellow
Write-Host "  Equipo:            $($adapter.Hostname)"
Write-Host "  Adaptador:         $($adapter.InterfaceAlias)"
Write-Host "  IP actual:         $($adapter.IPv4Address)"
Write-Host "  MAC:               $($adapter.MacAddress)"
Write-Host "  Subred:            $($adapter.SubnetCidr)"
Write-Host "  Broadcast WOL:     $($adapter.BroadcastAddress)"
Write-Host "  Puerto del agente: $AgentPort"
Write-Host ""

$homeAssistantIp = Read-DefaultValue -Prompt "IP de Home Assistant (deja vacio para permitir toda la subred)" -DefaultValue ""
$shutdownForce = (Read-DefaultValue -Prompt "Forzar cierre de aplicaciones al apagar? (s/n)" -DefaultValue "n") -eq "s"
$installAtStartup = (Read-DefaultValue -Prompt "Instalar el agente al arranque? (s/n)" -DefaultValue "s") -eq "s"
$createFirewallRule = (Read-DefaultValue -Prompt "Crear regla de firewall? (s/n)" -DefaultValue "s") -eq "s"

if ($homeAssistantIp) {
    $allowedSubnets = @("$homeAssistantIp/32", "127.0.0.1/32")
    $firewallRemoteAddresses = @($homeAssistantIp)
}
else {
    $allowedSubnets = @($adapter.SubnetCidr, "127.0.0.1/32")
    $firewallRemoteAddresses = @($adapter.SubnetCidr)
}

$configObject = [ordered]@{
    host                   = "0.0.0.0"
    port                   = $AgentPort
    token                  = $token
    allowed_subnets        = $allowedSubnets
    shutdown_delay_seconds = 0
    shutdown_force         = $shutdownForce
    log_file               = "pc_power_agent.log"
    machine_id             = $machineId
    pairing_code_hash      = Get-Sha256Hex -Value $pairingCode
    pairing_code_expires_at = [double]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + 600)
}

$configJson = $configObject | ConvertTo-Json -Depth 5
$configJson | Set-Content -Encoding UTF8 -Path $ConfigPath

if ($createFirewallRule) {
    if (-not $isAdmin) {
        Write-Warning "No estas en una consola de administrador. Se omite la regla de firewall."
    }
    else {
        & (Join-Path $agentDir "add-firewall-rule.ps1") -Port $AgentPort -RemoteAddresses $firewallRemoteAddresses
    }
}

if ($installAtStartup) {
    if (-not $isAdmin) {
        Write-Warning "No estas en una consola de administrador. Se omite la instalacion de la tarea programada."
    }
    else {
        & (Join-Path $agentDir "install-task.ps1") -TaskName $TaskName -ConfigPath $ConfigPath
    }
}

$haSummary = @"
PC Power Free - Datos para Home Assistant

Nombre sugerido: $($adapter.Hostname)
Host actual del PC: $($adapter.IPv4Address)
MAC: $($adapter.MacAddress)
Machine ID: $machineId
Codigo de vinculacion: $pairingCode
Puerto del agente: $AgentPort
Broadcast WOL: $($adapter.BroadcastAddress)
Subred de descubrimiento: $($adapter.SubnetCidr)

Notas:
- Home Assistant deberia descubrir este PC automaticamente en la red local
- Introduce el codigo de vinculacion al vincularlo desde Home Assistant
- Si el codigo caduca, vuelve a ejecutar este asistente para generar uno nuevo
"@

$summaryPath = Join-Path $agentDir "home_assistant_values.txt"
$haSummary | Set-Content -Encoding UTF8 -Path $summaryPath

try {
    Set-Clipboard -Value $haSummary
    $clipboardMessage = "El resumen tambien se ha copiado al portapapeles."
}
catch {
    $clipboardMessage = "No se pudo copiar el resumen al portapapeles."
}

Write-Host ""
Write-Host "Configuracion guardada en: $ConfigPath" -ForegroundColor Green
Write-Host "Resumen para Home Assistant: $summaryPath" -ForegroundColor Green
Write-Host $clipboardMessage -ForegroundColor Green
Write-Host ""
Write-Host $haSummary
