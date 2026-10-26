# Run in Windows PowerShell as Administrator. Changes only biometric service and
# the Egis USB 1c7a:05aa device; never touches biometric databases or PIN settings.
# Rollback: .\windows-disable-biometrics.ps1 -Restore 'C:\...\before.json'
#Requires -RunAsAdministrator
[CmdletBinding()]
param([string]$Restore)
$ErrorActionPreference = 'Stop'
$SensorPattern = '*VID_1C7A&PID_05AA*'
if ($Restore) {
    $Before = Get-Content -LiteralPath $Restore -Raw | ConvertFrom-Json
    if ($Before.ServiceName -ne 'WbioSrvc') { throw 'Unexpected backup service.' }
    if ($Before.StartMode -notin @('Auto', 'Manual', 'Disabled')) { throw 'Unexpected service mode.' }
    $Modes = @{ Auto = 'Automatic'; Manual = 'Manual'; Disabled = 'Disabled' }
    Set-Service -Name WbioSrvc -StartupType $Modes[$Before.StartMode]
    foreach ($Device in $Before.Devices) {
        if ($Device.InstanceId -notlike $SensorPattern) { throw 'Unexpected backup device.' }
        if ($Device.ConfigManagerErrorCode -ne 22) {
            Enable-PnpDevice -InstanceId $Device.InstanceId -Confirm:$false
        }
    }
    if ($Before.WasRunning) { Start-Service -Name WbioSrvc }
    Write-Host 'Previous service/device settings restored.'
    exit
}
$Service = Get-CimInstance Win32_Service -Filter "Name='WbioSrvc'"
if (-not $Service) { throw 'Windows Biometric Service not found.' }
$Devices = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPDeviceID -like $SensorPattern })
if (-not $Devices) { throw 'Egis 1c7a:05aa not found. No settings changed; inspect Device Manager.' }
$BackupDirectory = Join-Path $env:LOCALAPPDATA ('HonorFingerprint\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$Before = [ordered]@{
    Time = (Get-Date).ToString('o')
    ServiceName = 'WbioSrvc'
    StartMode = $Service.StartMode
    WasRunning = ($Service.State -eq 'Running')
    Devices = @($Devices | ForEach-Object { [ordered]@{
        InstanceId = $_.PNPDeviceID
        Name = $_.Name
        ConfigManagerErrorCode = $_.ConfigManagerErrorCode
    } })
}
$Backup = Join-Path $BackupDirectory 'before.json'
$Before | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Backup -Encoding UTF8
Write-Host "Backup: $Backup"
Set-Service -Name WbioSrvc -StartupType Disabled
Stop-Service -Name WbioSrvc -Force
foreach ($Device in $Devices) {
    if ($Device.ConfigManagerErrorCode -ne 22) {
        Disable-PnpDevice -InstanceId $Device.PNPDeviceID -Confirm:$false
    }
}
$After = Get-CimInstance Win32_Service -Filter "Name='WbioSrvc'"
$AfterDevices = @(Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPDeviceID -like $SensorPattern })
$After | Select-Object Name, State, StartMode | Format-Table -AutoSize
$AfterDevices | Select-Object Name, ConfigManagerErrorCode | Format-Table -AutoSize
if ($After.StartMode -ne 'Disabled' -or $After.State -ne 'Stopped') { throw 'Biometric service is not disabled/stopped.' }
if (@($AfterDevices | Where-Object { $_.ConfigManagerErrorCode -ne 22 }).Count -gt 0) { throw 'Sensor not disabled (expected Code 22).' }
Write-Host 'Windows biometrics disabled. PIN/password remain the sign-in methods.'
Write-Host 'Restart into Linux, then re-enroll and verify the finger there.'
Write-Host 'Persistence must still be checked after the next Windows -> Linux cycle.'
