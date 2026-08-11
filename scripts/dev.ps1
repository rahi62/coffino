param(
  [switch]$Electron,
  [switch]$NoWorkers,
  [switch]$SkipInfrastructure
)

$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$backendPath=Join-Path $root "backend"
$frontendPath=Join-Path $root "frontend"
$electronPath=Join-Path $root "electron"
$python=Join-Path $backendPath ".venv\Scripts\python.exe"

if (!(Test-Path $python)) {
  throw "Python environment was not found. Run scripts/setup-local.ps1 first."
}
if (!(Test-Path (Join-Path $frontendPath "node_modules"))) {
  throw "Frontend dependencies are missing. Run scripts/setup-local.ps1 first."
}
if (!(Test-Path (Join-Path $frontendPath ".env.local"))) {
  Copy-Item (Join-Path $frontendPath ".env.local.example") (Join-Path $frontendPath ".env.local")
}
foreach ($port in @(3000,8000)) {
  if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "Port $port is already in use. Stop the full Docker backend/frontend stack before starting local development."
  }
}
if (!$SkipInfrastructure) {
  & (Join-Path $PSScriptRoot "dev-infra.ps1")
}

$previousEnvFile=$env:DJANGO_ENV_FILE
try {
  $env:DJANGO_ENV_FILE="..\.env.dev"
  Push-Location $backendPath
  & $python manage.py migrate --noinput
  Pop-Location
} finally {
  if ($null -eq $previousEnvFile) { Remove-Item Env:DJANGO_ENV_FILE -ErrorAction SilentlyContinue }
  else { $env:DJANGO_ENV_FILE=$previousEnvFile }
}

function Start-DevTerminal([string]$path,[string]$command) {
  $script="Set-Location -LiteralPath '$path'; $command"
  Start-Process powershell.exe -ArgumentList @("-NoExit","-Command",$script)
}

$djangoEnv='$env:DJANGO_ENV_FILE="..\.env.dev";'
Start-DevTerminal $backendPath "$djangoEnv & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
Start-DevTerminal $frontendPath "npm.cmd run dev"

if (!$NoWorkers) {
  Start-DevTerminal $backendPath "$djangoEnv & .\.venv\Scripts\celery.exe -A config worker --loglevel=INFO --concurrency=2"
  Start-DevTerminal $backendPath "$djangoEnv & .\.venv\Scripts\celery.exe -A config beat --loglevel=INFO"
}
if ($Electron) {
  Start-DevTerminal $electronPath "npm.cmd run dev"
}

Write-Host "Development is ready: frontend http://localhost:3000 and backend http://127.0.0.1:8000" -ForegroundColor Green
