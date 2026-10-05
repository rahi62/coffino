#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY="$ROOT/deploy/vps"

for cmd in git node npm python3 psql nginx systemctl curl; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing required command: $cmd"; exit 1; }
done

sudo install -d -m 0750 /etc/cafino

if [[ ! -f /etc/cafino/backend.env ]]; then
  echo "Create /etc/cafino/backend.env from deploy/vps/backend.env.example before first activation."
  exit 1
fi
if [[ ! -f /etc/cafino/frontend.env ]]; then
  sudo install -m 0640 "$DEPLOY/frontend.env.example" /etc/cafino/frontend.env
fi

install_unit() {
  local template="$1"
  local target="$2"
  local tmp
  tmp="$(mktemp)"
  sed "s|__ROOT__|$ROOT|g" "$template" > "$tmp"
  sudo install -m 0644 "$tmp" "$target"
  rm -f "$tmp"
}

install_unit "$DEPLOY/systemd/cafino-backend.service" /etc/systemd/system/cafino-backend.service
install_unit "$DEPLOY/systemd/cafino-frontend.service" /etc/systemd/system/cafino-frontend.service
install_unit "$DEPLOY/systemd/cafino-worker.service" /etc/systemd/system/cafino-worker.service
install_unit "$DEPLOY/systemd/cafino-beat.service" /etc/systemd/system/cafino-beat.service

sudo systemctl daemon-reload
sudo systemctl enable cafino-backend.service cafino-frontend.service cafino-worker.service cafino-beat.service

"$DEPLOY/update.sh"

sudo install -m 0644 "$DEPLOY/nginx.conf" /etc/nginx/sites-available/cafino.conf
sudo ln -sfn /etc/nginx/sites-available/cafino.conf /etc/nginx/sites-enabled/cafino.conf
sudo nginx -t
sudo systemctl reload nginx

echo "Native Cafino services installed."
