$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$backend="$root\backend";$frontend="$root\frontend";$electron="$root\electron"
if (!(Test-Path "$backend\.venv")) { throw "Run scripts/setup-local.ps1 first." }
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

Set-Location $electron
npm install
npm run build
Write-Host "Release created under electron\release" -ForegroundColor Green
