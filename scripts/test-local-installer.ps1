param(
  [string]$Installer="",
  [switch]$Build,
  [switch]$RequireTrustedSignature
)

$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot

function Assert-Port-Free([int]$Port){
  $listener=Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
  if($listener){throw "Port $Port is already in use by PID $($listener.OwningProcess). Close the old Cafino/dev process before the installer test."}
}

if($Build){
  Write-Host "Preparing local build dependencies..." -ForegroundColor Cyan
  & "$root\scripts\setup-local.ps1"
  Write-Host "Building an unsigned Local pilot installer..." -ForegroundColor Cyan
  & "$root\scripts\build-release.ps1" -Channel stable
}

if([string]::IsNullOrWhiteSpace($Installer)){
  $candidate=Get-ChildItem "$root\electron\release" -Filter "Cafino-Setup-*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if(-not $candidate){throw "No Cafino installer found. Pass -Installer or run with -Build."}
  $Installer=$candidate.FullName
}

$installerPath=(Resolve-Path $Installer).Path
$drive=Get-PSDrive -Name ([IO.Path]::GetPathRoot($installerPath).TrimEnd('\').TrimEnd(':')) -ErrorAction SilentlyContinue
if($drive -and $drive.Free -lt 2GB){throw "At least 2 GB free disk space is required for a safe pilot install/test."}

Assert-Port-Free 8000
Assert-Port-Free 3000

Write-Host "Running Electron POS adapter contract tests..." -ForegroundColor Cyan
Push-Location "$root\electron"
try{
  node src/device-adapters.test.js
  if($LASTEXITCODE -ne 0){throw "POS/device adapter contract failed."}
}finally{Pop-Location}

Write-Host "Installing, verifying packaged runtime, and uninstalling Cafino..." -ForegroundColor Cyan
& "$root\scripts\smoke-test-installer.ps1" -Installer $installerPath -RequireTrustedSignature:$RequireTrustedSignature

Write-Host "" 
Write-Host "Cafino Local installer acceptance PASSED." -ForegroundColor Green
Write-Host "Installer: $installerPath"
Write-Host "Next real-device checks: printer mapping, one POS sale/decline, backup->restore drill, offline restart, and update/rollback." -ForegroundColor Yellow
