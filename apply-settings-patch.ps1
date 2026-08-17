param([string]$ProjectRoot="",[switch]$Force,[switch]$Validate)
$ErrorActionPreference="Stop"
$PatchRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot=Join-Path $PatchRoot "payload"
$manifest=Get-Content (Join-Path $PatchRoot "patch-manifest.json") -Raw | ConvertFrom-Json
function Resolve-Project([string]$candidate){
 if($candidate){return (Resolve-Path $candidate).Path}
 $cwd=(Get-Location).Path
 if((Test-Path (Join-Path $cwd "backend")) -and (Test-Path (Join-Path $cwd "frontend"))){return $cwd}
 $parent=Split-Path -Parent $PatchRoot
 if((Test-Path (Join-Path $parent "backend")) -and (Test-Path (Join-Path $parent "frontend"))){return $parent}
 throw "ProjectRoot مشخص نیست. -ProjectRoot را بدهید."
}
function Hash([string]$p){if(!(Test-Path $p -PathType Leaf)){return $null};return (Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$ProjectRoot=Resolve-Project $ProjectRoot
if(!(Test-Path (Join-Path $ProjectRoot "backend")) -or !(Test-Path (Join-Path $ProjectRoot "frontend"))){throw "مسیر پروژه Cafino معتبر نیست: $ProjectRoot"}
$conflicts=@()
foreach($e in $manifest.entries){
 $rel=$e.path -replace '/', [IO.Path]::DirectorySeparatorChar;$target=Join-Path $ProjectRoot $rel;$current=Hash $target;$new=$e.new_sha256.ToLowerInvariant();$base=if($e.base_sha256){$e.base_sha256.ToLowerInvariant()}else{$null}
 if($current -eq $new){continue}
 if($e.status -eq "new") {if($current -ne $null){$conflicts+=$e.path}}
 elseif($current -ne $base){$conflicts+=$e.path}
}
if($conflicts.Count -and -not $Force){Write-Host "Conflict: فایل‌های زیر بعد از ZIP پایه تغییر کرده‌اند:" -ForegroundColor Red;$conflicts|%{Write-Host " - $_" -ForegroundColor Red};exit 2}
$stamp=Get-Date -Format "yyyyMMdd-HHmmss";$backup=Join-Path $ProjectRoot "patch-backups\settings-dashboard-$stamp";New-Item -ItemType Directory -Force $backup|Out-Null;$copied=0
foreach($e in $manifest.entries){
 $rel=$e.path -replace '/', [IO.Path]::DirectorySeparatorChar;$source=Join-Path $PayloadRoot $rel;$target=Join-Path $ProjectRoot $rel
 if((Hash $target) -eq $e.new_sha256.ToLowerInvariant()){continue}
 if(Test-Path $target -PathType Leaf){$b=Join-Path $backup $rel;New-Item -ItemType Directory -Force (Split-Path -Parent $b)|Out-Null;Copy-Item $target $b -Force}
 New-Item -ItemType Directory -Force (Split-Path -Parent $target)|Out-Null;Copy-Item $source $target -Force;$copied++
}
Copy-Item (Join-Path $PatchRoot "patch-manifest.json") (Join-Path $backup "patch-manifest.json") -Force
Write-Host "Patch applied: $copied files. Backup: $backup" -ForegroundColor Green
$py=Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"
if(Test-Path $py){Push-Location (Join-Path $ProjectRoot "backend");try{& $py manage.py migrate --noinput;if($LASTEXITCODE){throw "migrate failed"};& $py manage.py check;if($LASTEXITCODE){throw "django check failed"};if($Validate){& $py manage.py test apps.core.tests_settings_dashboard --verbosity 2;if($LASTEXITCODE){throw "settings tests failed"}}}finally{Pop-Location}}else{Write-Warning "backend/.venv پیدا نشد؛ قبل از اجرا python manage.py migrate را انجام دهید."}
if($Validate){$nm=Join-Path $ProjectRoot "frontend\node_modules";if(Test-Path $nm){Push-Location (Join-Path $ProjectRoot "frontend");try{npm run build;if($LASTEXITCODE){throw "Next build failed"}}finally{Pop-Location}}else{Write-Warning "frontend/node_modules موجود نیست؛ Next build اجرا نشد."}}
Write-Host "Settings Hub ready at /settings" -ForegroundColor Cyan
