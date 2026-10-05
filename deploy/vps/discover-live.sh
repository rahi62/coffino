#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-cafeno.digitalafarin.ir}"

section(){ printf '\n===== %s =====\n' "$1"; }

section "HOST"
hostname || true
uname -a || true
df -h / || true
free -h || true

section "DOMAIN HTTP"
curl -kfsSI --max-time 8 "https://$DOMAIN/" || true
curl -kfsS --max-time 8 "https://$DOMAIN/api/v1/health/" || true
printf '\n'

section "NGINX ROUTE"
if command -v nginx >/dev/null 2>&1; then
  sudo nginx -T 2>/dev/null | awk -v domain="$DOMAIN" '
    BEGIN { capture=0; depth=0; found=0 }
    /server[[:space:]]*\{/ {
      block=$0 "\n"; capture=1; depth=1; next
    }
    capture {
      block=block $0 "\n"
      opens=gsub(/\{/,"{")
      closes=gsub(/\}/,"}")
      depth += opens-closes
      if ($0 ~ "server_name[[:space:]].*" domain) found=1
      if (depth<=0) {
        if(found) printf "%s", block
        block=""; capture=0; depth=0; found=0
      }
    }'
else
  echo "nginx: not installed"
fi

section "LISTENING PORTS"
sudo ss -ltnp 2>/dev/null | grep -E ':(80|443|3000|3001|3002|8000|8001|8002|9860|9861)\b' || true

section "CAF INO SYSTEMD"
sudo systemctl list-unit-files --type=service --no-pager 2>/dev/null | grep -Ei 'cafi|coffi' || true
sudo systemctl list-units --type=service --all --no-pager 2>/dev/null | grep -Ei 'cafi|coffi' || true

section "APP PROCESSES"
mapfile -t PIDS < <(pgrep -f 'next( |$)|next-server|node .*server|gunicorn|celery|manage.py runserver' || true)
for pid in "${PIDS[@]:-}"; do
  [[ -r "/proc/$pid/cmdline" ]] || continue
  cmd="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  user="$(ps -o user= -p "$pid" 2>/dev/null | xargs || true)"
  printf 'PID=%s USER=%s\nCWD=%s\nCMD=%s\n---\n' "$pid" "$user" "$cwd" "$cmd"
done

section "PM2"
if command -v pm2 >/dev/null 2>&1; then
  pm2 ls || true
else
  echo "pm2: not installed"
fi

section "REPOSITORY CANDIDATES"
roots=(/opt /srv /var/www /home/deploy /root)
for root in "${roots[@]}"; do
  [[ -d "$root" ]] || continue
  while IFS= read -r gitdir; do
    repo="${gitdir%/.git}"
    origin="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
    if printf '%s' "$origin" | grep -Eqi 'rahi62/(coffino|cafino)(\.git)?$'; then
      printf 'PATH=%s\nORIGIN=%s\nHEAD=%s\nBRANCH=%s\n---\n' \
        "$repo" "$origin" \
        "$(git -C "$repo" rev-parse HEAD 2>/dev/null || true)" \
        "$(git -C "$repo" branch --show-current 2>/dev/null || true)"
    fi
  done < <(sudo find "$root" -maxdepth 6 -type d -name .git -print 2>/dev/null)
done

section "POSTGRESQL"
if command -v psql >/dev/null 2>&1; then
  sudo systemctl is-active postgresql 2>/dev/null || true
  sudo -u postgres psql -Atqc "select datname from pg_database where datistemplate=false order by datname;" 2>/dev/null || echo "database list unavailable"
else
  echo "psql: not installed"
fi

section "REDIS"
sudo systemctl is-active redis-server 2>/dev/null || sudo systemctl is-active redis 2>/dev/null || true
redis-cli ping 2>/dev/null || true

section "KNOWN CAFINO CONFIG FILES (NAMES ONLY)"
sudo find /etc /opt /srv /var/www /home/deploy -maxdepth 6 -type f \
  \( -iname '*cafino*' -o -iname '*cafeno*' -o -iname '*coffino*' \) \
  -print 2>/dev/null | head -n 200 || true

section "DONE"
echo "Discovery completed without reading environment variable values or application secrets."
