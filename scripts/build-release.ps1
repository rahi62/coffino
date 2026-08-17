param(
  [switch]$Production,
  [switch]$AllowUnsigned
)

$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$backend="$root\backend";$frontend="$root\frontend";$electron="$root\electron"

function Require-Env([string]$Name) {
  $value=[Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($value)) { throw "$Name is required." }
  return $value
}
function Env-Or([string]$Name,$Fallback) {
  $value=[Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($value)) { return $Fallback }
  return $value
}
function Write-Utf8NoBom([string]$Path,[string]$Text) {
  $encoding=New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path,$Text,$encoding)
}

if (!(Test-Path "$backend\.venv")) { throw "Run scripts/setup-local.ps1 first." }

$updateUrl=""
$licensePublicKeyPath=""
if ($Production) {
  $updateUrl=Require-Env "CAF_INO_UPDATE_URL"
  if ($updateUrl -notmatch '^https://') { throw "CAF_INO_UPDATE_URL must use HTTPS." }
  $licensePublicKeyPath=Require-Env "CAF_INO_LICENSE_PUBLIC_KEY_PATH"
  if (!(Test-Path $licensePublicKeyPath)) { throw "CAF_INO_LICENSE_PUBLIC_KEY_PATH does not exist: $licensePublicKeyPath" }
  if (!$AllowUnsigned) {
    [void](Require-Env "CSC_LINK")
    [void](Require-Env "CSC_KEY_PASSWORD")
  }
}

& "$backend\.venv\Scripts\python.exe" "$root\scripts\release-check.py"
Set-Location $backend
& ".\.venv\Scripts\python.exe" manage.py makemigrations --check --dry-run
& ".\.venv\Scripts\python.exe" manage.py migrate
& ".\.venv\Scripts\python.exe" manage.py check --deploy
& ".\.venv\Scripts\python.exe" manage.py test
& ".\.venv\Scripts\pyinstaller.exe" --clean --noconfirm cafino-backend.spec

Remove-Item "$electron\release-resources" -Recurse -Force -ErrorAction SilentlyContinue
New-Item "$electron\release-resources\backend" -ItemType Directory -Force | Out-Null
Copy-Item "$backend\dist\cafino-backend.exe" "$electron\release-resources\backend\cafino-backend.exe"

Set-Location $frontend
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api/v1"
$env:NEXT_PUBLIC_API_ROOT="http://127.0.0.1:8000"
npm install
npm run build
New-Item "$electron\release-resources\frontend" -ItemType Directory -Force | Out-Null
Copy-Item ".next\standalone\*" "$electron\release-resources\frontend" -Recurse -Force
New-Item "$electron\release-resources\frontend\.next\static" -ItemType Directory -Force | Out-Null
Copy-Item ".next\static\*" "$electron\release-resources\frontend\.next\static" -Recurse -Force
if (Test-Path "public") { Copy-Item "public" "$electron\release-resources\frontend\public" -Recurse -Force }

New-Item "$electron\release-resources\config" -ItemType Directory -Force | Out-Null
$config=[ordered]@{
  updateUrl=$updateUrl
  enforceLicense=[bool]$Production
  licensePublicKey=if($Production){"config/license-public-key.pem"}else{""}
  backupIntervalHours=[int](Env-Or "CAF_INO_BACKUP_INTERVAL_HOURS" 24)
  backupRetentionCount=[int](Env-Or "CAF_INO_BACKUP_RETENTION_COUNT" 14)
  backupMaxAgeDays=[int](Env-Or "CAF_INO_BACKUP_MAX_AGE_DAYS" 60)
}
Write-Utf8NoBom "$electron\release-resources\config\release-config.json" ($config|ConvertTo-Json -Depth 4)
if ($Production) { Copy-Item $licensePublicKeyPath "$electron\release-resources\config\license-public-key.pem" -Force }

Set-Location $electron
$env:CAF_INO_PRODUCTION_BUILD=if($Production){"1"}else{"0"}
$env:CAF_INO_ALLOW_UNSIGNED=if($AllowUnsigned){"1"}else{"0"}
$env:CAF_INO_UPDATE_URL=$updateUrl
npm install
npm run test:release
npm run build

$releaseDir="$electron\release"
$manifest=[ordered]@{created_at=(Get-Date).ToUniversalTime().ToString("o");production=[bool]$Production;unsigned=[bool]$AllowUnsigned;artifacts=@()}
Get-ChildItem $releaseDir -File | Where-Object { $_.Extension -in '.exe','.yml','.blockmap' } | ForEach-Object {
  $hash=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  $manifest.artifacts+=@{name=$_.Name;size=$_.Length;sha256=$hash}
}
Write-Utf8NoBom "$releaseDir\release-manifest.json" ($manifest|ConvertTo-Json -Depth 6)
Write-Host "Release created under electron\release" -ForegroundColor Green
if($Production -and !$AllowUnsigned){Write-Host "Production signing gate was required." -ForegroundColor Green}
