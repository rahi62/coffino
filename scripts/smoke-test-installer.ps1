param(
  [Parameter(Mandatory=$true)][string]$Installer,
  [switch]$RequireTrustedSignature
)

$ErrorActionPreference="Stop"
$installer=(Resolve-Path $Installer).Path
$signature=Get-AuthenticodeSignature $installer
if($RequireTrustedSignature -and $signature.Status -ne "Valid"){
  throw "Installer Authenticode signature is not valid: $($signature.Status)"
}

$before=@(Get-ChildItem "$env:LOCALAPPDATA\Programs" -Filter "Cafino.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
$p=Start-Process -FilePath $installer -ArgumentList "/S" -Wait -PassThru
if($p.ExitCode -ne 0){throw "Silent NSIS install failed with exit code $($p.ExitCode)"}

$exe=Get-ChildItem "$env:LOCALAPPDATA\Programs" -Filter "Cafino.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $exe){
  $exe=Get-ChildItem "$env:ProgramFiles" -Filter "Cafino.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
}
if(-not $exe){throw "Installed Cafino.exe was not found."}

$smoke=Join-Path $env:RUNNER_TEMP "cafino-smoke.json"
Remove-Item $smoke -Force -ErrorAction SilentlyContinue
$env:CAF_INO_SMOKE_OUTPUT=$smoke
$app=Start-Process -FilePath $exe.FullName -ArgumentList "--cafino-smoke-check" -Wait -PassThru
if($app.ExitCode -ne 0){throw "Packaged Cafino smoke check failed with exit code $($app.ExitCode)"}
if(!(Test-Path $smoke)){throw "Packaged Cafino did not produce smoke output."}
$result=Get-Content $smoke -Raw | ConvertFrom-Json
if(-not $result.ok){throw "Packaged Cafino smoke check returned failure: $($result | ConvertTo-Json -Compress)"}
Write-Host ($result | ConvertTo-Json -Depth 5)

$uninstaller=Join-Path $exe.DirectoryName "Uninstall Cafino.exe"
if(Test-Path $uninstaller){
  $u=Start-Process -FilePath $uninstaller -ArgumentList "/S" -Wait -PassThru
  if($u.ExitCode -ne 0){throw "Silent uninstall failed with exit code $($u.ExitCode)"}
}

Write-Host "Cafino clean Windows installer smoke test passed." -ForegroundColor Green
