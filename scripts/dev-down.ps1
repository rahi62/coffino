$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  docker compose --env-file .env.dev -f docker-compose.dev.yml down
} finally {
  Pop-Location
}
