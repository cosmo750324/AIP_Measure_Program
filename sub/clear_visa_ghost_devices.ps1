# Removes stale (non-present) USBTMC / GPIB device records from Windows so
# NI-VISA / Keysight IO Libraries stop surfacing them as "ghost" VISA resources.
# Only targets Class in USBTestAndMeasurementDevice / GPIB Interfaces / GPIB,
# and only devices whose Status is 'Unknown' (not currently connected).
# Currently-connected instruments and all other USB devices (flash drives,
# hubs, U2C-12 adapters, audio devices, etc.) are never touched.
#
# Must be run as Administrator. Right-click PowerShell -> "Run as administrator",
# then: cd to this folder and run  .\clear_visa_ghost_devices.ps1

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please re-run this script as Administrator (right-click PowerShell -> Run as administrator)." -ForegroundColor Red
    exit 1
}

$targets = Get-PnpDevice | Where-Object {
    $_.Status -eq 'Unknown' -and $_.Class -in @('USBTestAndMeasurementDevice', 'GPIB Interfaces', 'GPIB')
}

if (-not $targets) {
    Write-Host "No matching ghost device records found." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($targets.Count) non-present USBTMC / GPIB device record(s):" -ForegroundColor Cyan
$targets | Select-Object FriendlyName, Class, InstanceId | Format-Table -AutoSize

$answer = Read-Host "Remove all of the above device records? (they will reinstall automatically if plugged in again) [y/N]"
if ($answer -ne 'y' -and $answer -ne 'Y') {
    Write-Host "Cancelled, nothing was removed."
    exit 0
}

$ok = 0
$fail = 0
foreach ($dev in $targets) {
    try {
        Remove-PnpDevice -InstanceId $dev.InstanceId -Confirm:$false -ErrorAction Stop
        $ok++
    } catch {
        $fail++
        Write-Host "Failed to remove: $($dev.FriendlyName) [$($dev.InstanceId)] - $_" -ForegroundColor Red
    }
}

Write-Host "Done. Removed $ok, failed $fail." -ForegroundColor Green
