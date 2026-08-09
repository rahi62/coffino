$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
if (Test-Path "$root\frontend\app") { throw "Stale frontend/app detected. Extract Cafino into a clean directory." }
Set-Location "$root\backend"
if (!(Test-Path ".venv")) { py -3.12 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements-dev.txt
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
& ".\.venv\Scripts\python.exe" manage.py makemigrations --check --dry-run
& ".\.venv\Scripts\python.exe" manage.py migrate
& ".\.venv\Scripts\python.exe" manage.py seed_demo
Set-Location "$root\frontend"; npm install
Set-Location "$root\electron"; npm install
Write-Host "Cafino local setup complete." -ForegroundColor Green
