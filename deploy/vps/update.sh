#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

for cmd in git node npm python3 systemctl curl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing required command: $cmd"; exit 1; }
done

test -f /etc/cafino/backend.env || { echo "Missing /etc/cafino/backend.env"; exit 1; }
test -f /etc/cafino/frontend.env || { echo "Missing /etc/cafino/frontend.env"; exit 1; }

git fetch origin main
git checkout main
git pull --ff-only origin main

python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt

set -a
source /etc/cafino/backend.env
set +a
backend/.venv/bin/python backend/manage.py migrate --noinput
backend/.venv/bin/python backend/manage.py collectstatic --noinput

set -a
source /etc/cafino/frontend.env
set +a
cd frontend
npm ci
npm run build
cd "$ROOT"

sudo systemctl restart cafino-backend.service
sudo systemctl restart cafino-worker.service
sudo systemctl restart cafino-beat.service
sudo systemctl restart cafino-frontend.service

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:9860/api/v1/health/ >/dev/null; then
    break
  fi
  if [[ "$i" == "30" ]]; then
    sudo systemctl status cafino-backend.service --no-pager
    exit 1
  fi
  sleep 2
done

curl -fsSI http://127.0.0.1:9861/login >/dev/null
echo "Cafino native update completed."
git rev-parse HEAD
