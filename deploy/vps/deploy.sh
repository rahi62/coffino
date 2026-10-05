#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <domain> [letsencrypt-email]"
  exit 1
fi

DOMAIN="$1"
EMAIL="${2:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_DIR="$ROOT/deploy/vps"
ENV_FILE="$DEPLOY_DIR/.env.vps"
BACKEND_PORT="${CAF_INO_BACKEND_PORT:-9860}"
FRONTEND_PORT="${CAF_INO_FRONTEND_PORT:-9861}"

for cmd in git docker openssl curl nginx sed; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing required command: $cmd"; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is required."; exit 1; }

check_port() {
  local port="$1"
  if command -v ss >/dev/null 2>&1 && ss -ltn | awk '{print $4}' | grep -Eq "[:.]$port$"; then
    echo "Port $port is already listening. Set CAF_INO_BACKEND_PORT / CAF_INO_FRONTEND_PORT to free ports."
    exit 1
  fi
}

if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  cat > "$ENV_FILE" <<EOF
CAF_INO_DOMAIN=$DOMAIN
CAF_INO_BACKEND_PORT=$BACKEND_PORT
CAF_INO_FRONTEND_PORT=$FRONTEND_PORT
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DJANGO_SECRET_KEY=$(openssl rand -hex 48)
CAF_INO_BUSINESS_NAME=Cafino
CAF_INO_BRANCH_NAME=Main
CAF_INO_OWNER_USERNAME=
CAF_INO_OWNER_EMAIL=
CAF_INO_BOOTSTRAP_OWNER_PASSWORD=
EOF
else
  sed -i "s/^CAF_INO_DOMAIN=.*/CAF_INO_DOMAIN=$DOMAIN/" "$ENV_FILE"
  BACKEND_PORT="$(grep '^CAF_INO_BACKEND_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
  FRONTEND_PORT="$(grep '^CAF_INO_FRONTEND_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
  BACKEND_PORT="${BACKEND_PORT:-9860}"
  FRONTEND_PORT="${FRONTEND_PORT:-9861}"
fi

check_port "$BACKEND_PORT"
check_port "$FRONTEND_PORT"

cd "$ROOT"
git fetch origin main
git checkout main
git pull --ff-only origin main

docker compose --env-file "$ENV_FILE" -f "$DEPLOY_DIR/compose.prod.yml" up -d --build

echo "Waiting for backend health..."
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$BACKEND_PORT/api/v1/health/" >/dev/null; then
    break
  fi
  if [[ "$i" == "60" ]]; then
    docker compose --env-file "$ENV_FILE" -f "$DEPLOY_DIR/compose.prod.yml" ps
    docker compose --env-file "$ENV_FILE" -f "$DEPLOY_DIR/compose.prod.yml" logs --tail=120 backend
    exit 1
  fi
  sleep 2
done

set -a
source "$ENV_FILE"
set +a

if [[ -n "${CAF_INO_OWNER_USERNAME:-}" && -n "${CAF_INO_BOOTSTRAP_OWNER_PASSWORD:-}" ]]; then
  docker compose --env-file "$ENV_FILE" -f "$DEPLOY_DIR/compose.prod.yml" exec -T \
    -e CAF_INO_BOOTSTRAP_OWNER_PASSWORD="$CAF_INO_BOOTSTRAP_OWNER_PASSWORD" backend \
    python manage.py bootstrap_business_owner \
      --business-name "${CAF_INO_BUSINESS_NAME:-Cafino}" \
      --branch-name "${CAF_INO_BRANCH_NAME:-Main}" \
      --username "$CAF_INO_OWNER_USERNAME" \
      --email "${CAF_INO_OWNER_EMAIL:-}" \
      --deployment-type SAAS
fi

TMP_CONF="$(mktemp)"
sed \
  -e "s/__CAF_INO_DOMAIN__/$DOMAIN/g" \
  -e "s/__CAF_INO_BACKEND_PORT__/$BACKEND_PORT/g" \
  -e "s/__CAF_INO_FRONTEND_PORT__/$FRONTEND_PORT/g" \
  "$DEPLOY_DIR/nginx.conf.template" > "$TMP_CONF"

sudo install -m 0644 "$TMP_CONF" /etc/nginx/sites-available/cafino.conf
sudo ln -sfn /etc/nginx/sites-available/cafino.conf /etc/nginx/sites-enabled/cafino.conf
rm -f "$TMP_CONF"
sudo nginx -t
sudo systemctl reload nginx

if [[ -n "$EMAIL" ]]; then
  command -v certbot >/dev/null 2>&1 || { echo "certbot is not installed."; exit 1; }
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect
  sudo nginx -t
  sudo systemctl reload nginx
else
  echo "TLS not requested. Run certbot before using this public deployment:"
  echo "  sudo certbot --nginx -d $DOMAIN"
fi

echo "Backend:  http://127.0.0.1:$BACKEND_PORT/api/v1/health/"
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT/"
echo "Public:   https://$DOMAIN"
