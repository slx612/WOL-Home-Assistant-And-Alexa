param(
    [string]$TaskName = "PC Power Agent"
)

$ErrorActionPreference = "Stop"

Get-Process -Name "PCPowerTray" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarea eliminada: $TaskName"
}
else {
    Write-Host "No existe la tarea $TaskName"
}

Remove-ItemProperty `
    -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" `
    -Name "PC Power Free Tray" `
    -ErrorAction SilentlyContinue
