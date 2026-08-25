$DistRoot = "D:\DairyOS\dist-installer"
$TargetDesktop = "C:\Users\ammad\Desktop\DairyOS_USB_Installer"

if (-not (Test-Path $TargetDesktop)) {
    New-Item -ItemType Directory -Path $TargetDesktop -Force | Out-Null
}

$Exe = Get-ChildItem -Path $DistRoot -Filter "*.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($Exe) {
    Copy-Item -Path $Exe.FullName -Destination (Join-Path $TargetDesktop $Exe.Name) -Force
    Write-Host "Successfully copied $($Exe.Name) to $TargetDesktop" -ForegroundColor Green
} else {
    Write-Host "Build output not found yet in $DistRoot" -ForegroundColor Yellow
}
