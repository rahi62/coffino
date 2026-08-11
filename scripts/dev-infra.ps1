$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$envFile=Join-Path $root ".env.dev"
$exampleFile=Join-Path $root ".env.dev.example"

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker Desktop is not available. Start it and try again."
}
if (!(Test-Path $envFile)) {
  Copy-Item $exampleFile $envFile
  Write-Host ".env.dev was created from the local development example." -ForegroundColor Yellow
}

Push-Location $root
try {
  docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --wait --wait-timeout 60
} finally {
  Pop-Location
}
Write-Host "Development infrastructure is ready: PostgreSQL on 5433 and Redis on 6380." -ForegroundColor Green
