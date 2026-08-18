param(
  [Parameter(Mandatory=$true)][string]$Installer,
  [switch]$RequireTrustedSignature,
  [switch]$RuntimeSmoke,
  [switch]$AllowExistingInstall
)

$ErrorActionPreference="Stop"
$installer=(Resolve-Path $Installer).Path
$signature=Get-AuthenticodeSignature $installer
if($RequireTrustedSignature -and $signature.Status -ne "Valid"){
  throw "Installer Authenticode signature is not valid: $($signature.Status)"
}

function Find-CafinoExecutables {
  $rows=@()
  if(Test-Path "$env:LOCALAPPDATA\Programs"){
    $rows+=@(Get-ChildItem "$env:LOCALAPPDATA\Programs" -Filter "Cafino.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  }
  if($env:ProgramFiles -and (Test-Path $env:ProgramFiles)){
    $rows+=@(Get-ChildItem $env:ProgramFiles -Filter "Cafino.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  }
  return @($rows | Sort-Object -Unique)
}

function Wait-Http200([string]$Url,[int]$Attempts=120,[int]$DelayMs=1000){
  $last=""
  for($i=0;$i -lt $Attempts;$i++){
    try{
      $response=Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -MaximumRedirection 0 -ErrorAction Stop
      if([int]$response.StatusCode -eq 200){return $response}
      $last="HTTP $($response.StatusCode)"
    }catch{
      if($_.Exception.Response){
        try{$last="HTTP $([int]$_.Exception.Response.StatusCode)"}catch{$last=$_.Exception.Message}
      }else{$last=$_.Exception.Message}
    }
    Start-Sleep -Milliseconds $DelayMs
  }
  throw "Timed out waiting for exact HTTP 200 from $Url. Last result: $last"
}

function Stop-ProcessTree([int]$Pid){
  try{& taskkill.exe /PID $Pid /T /F 2>$null | Out-Null}catch{}
}

$before=Find-CafinoExecutables
$userDataPath=Join-Path $env:APPDATA "Cafino"
$userDataExisted=Test-Path $userDataPath
if(-not $AllowExistingInstall){
  if($before.Count -gt 0){
    throw "A Cafino installation already exists. Clean-pilot smoke refuses to risk testing an old binary. Uninstall it first or explicitly pass -AllowExistingInstall. Existing: $($before -join ', ')"
  }
  if($userDataExisted){
    throw "Existing Cafino user data was found at $userDataPath. A clean first-run test must not overwrite or mistake preserved customer data for a fresh installation. Move/backup it first or explicitly pass -AllowExistingInstall."
  }
}

$installedByThisRun=$false
try{
  $p=Start-Process -FilePath $installer -ArgumentList "/S" -Wait -PassThru
  if($p.ExitCode -ne 0){throw "Silent NSIS install failed with exit code $($p.ExitCode)"}
  $installedByThisRun=$true

  $after=Find-CafinoExecutables
  $newPaths=@($after | Where-Object {$_ -notin $before})
  if($newPaths.Count -gt 0){
    $exe=Get-Item ($newPaths | Select-Object -First 1)
  }elseif($AllowExistingInstall -and $after.Count -gt 0){
    $exe=Get-Item ($after | Sort-Object { (Get-Item $_).LastWriteTimeUtc } -Descending | Select-Object -First 1)
  }else{
    throw "Installed Cafino.exe was not found as a new installation."
  }

  $smoke=Join-Path $env:TEMP "cafino-smoke-$PID.json"
  Remove-Item $smoke -Force -ErrorAction SilentlyContinue
  $previousSmokeOutput=$env:CAF_INO_SMOKE_OUTPUT
  $env:CAF_INO_SMOKE_OUTPUT=$smoke
  try{
    $app=Start-Process -FilePath $exe.FullName -ArgumentList "--cafino-smoke-check" -Wait -PassThru
    if($app.ExitCode -ne 0){throw "Packaged Cafino smoke check failed with exit code $($app.ExitCode)"}
    if(!(Test-Path $smoke)){throw "Packaged Cafino did not produce smoke output."}
    $result=Get-Content $smoke -Raw | ConvertFrom-Json
    if(-not $result.ok){throw "Packaged Cafino smoke check returned failure: $($result | ConvertTo-Json -Compress)"}
    Write-Host ($result | ConvertTo-Json -Depth 5)
  }finally{
    if($null -eq $previousSmokeOutput){Remove-Item Env:CAF_INO_SMOKE_OUTPUT -ErrorAction SilentlyContinue}else{$env:CAF_INO_SMOKE_OUTPUT=$previousSmokeOutput}
    Remove-Item $smoke -Force -ErrorAction SilentlyContinue
  }

  if($RuntimeSmoke){
    Write-Host "Starting installed Cafino for real Local runtime smoke..." -ForegroundColor Cyan
    $runtime=$null
    try{
      $runtime=Start-Process -FilePath $exe.FullName -PassThru
      $health=Wait-Http200 "http://127.0.0.1:8000/api/v1/health/"
      $healthJson=$health.Content | ConvertFrom-Json
      if($healthJson.status -ne "ok" -or $healthJson.service -ne "cafino-backend"){
        throw "Backend health payload is not the Cafino health contract."
      }
      Wait-Http200 "http://127.0.0.1:3000/login" | Out-Null

      if(-not $userDataExisted){
        $bootstrap=Wait-Http200 "http://127.0.0.1:8000/api/v1/local/bootstrap/"
        $bootstrapJson=$bootstrap.Content | ConvertFrom-Json
        if(-not $bootstrapJson.available -or -not $bootstrapJson.needs_setup){
          throw "Fresh installed database did not expose the expected one-shot Local first-run setup state."
        }
      }
      Write-Host "Installed Backend, Frontend and fresh Local first-run state passed runtime smoke." -ForegroundColor Green
    }finally{
      if($runtime){Stop-ProcessTree $runtime.Id}
      Start-Sleep -Seconds 2
    }
  }

  $uninstaller=Join-Path $exe.DirectoryName "Uninstall Cafino.exe"
  if(!(Test-Path $uninstaller)){throw "Cafino uninstaller was not found next to the installed executable."}
  $u=Start-Process -FilePath $uninstaller -ArgumentList "/S" -Wait -PassThru
  if($u.ExitCode -ne 0){throw "Silent uninstall failed with exit code $($u.ExitCode)"}
  $installedByThisRun=$false

  if(-not $userDataExisted -and (Test-Path $userDataPath)){
    Remove-Item $userDataPath -Recurse -Force
  }

  Write-Host "Cafino clean Windows installer smoke test passed." -ForegroundColor Green
  Write-Host "Installed executable tested: $($exe.FullName)"
}finally{
  if($installedByThisRun){
    $current=Find-CafinoExecutables | Select-Object -First 1
    if($current){
      $fallbackUninstaller=Join-Path (Split-Path -Parent $current) "Uninstall Cafino.exe"
      if(Test-Path $fallbackUninstaller){try{Start-Process -FilePath $fallbackUninstaller -ArgumentList "/S" -Wait | Out-Null}catch{}}
    }
  }
  if(-not $userDataExisted -and (Test-Path $userDataPath)){
    try{Remove-Item $userDataPath -Recurse -Force}catch{}
  }
}
