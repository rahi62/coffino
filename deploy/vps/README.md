# Cafino VPS deployment

This deployment runs the full Cafino stack with Docker Compose and exposes it through one public domain.

Routing:

- `https://DOMAIN/` -> Next.js frontend
- `https://DOMAIN/api/*` -> Django API
- `https://DOMAIN/admin/*` -> Django admin
- `https://DOMAIN/static/*` -> Django/WhiteNoise

Default localhost-only ports are `9861` for frontend and `9860` for backend to avoid colliding with existing services on the VPS.

## DNS

Point the selected domain's A/AAAA record to the VPS before requesting Let's Encrypt.

## Deploy

From the repository root on the VPS:

```bash
chmod +x deploy/vps/deploy.sh
./deploy/vps/deploy.sh cafino.example.com you@example.com
```

The first run creates `deploy/vps/.env.vps` with random database and Django secrets. The file is intentionally not committed.

To bootstrap the first owner on a fresh database, edit that file and set:

```dotenv
CAF_INO_BUSINESS_NAME=Cafino
CAF_INO_BRANCH_NAME=Main
CAF_INO_OWNER_USERNAME=your-user
CAF_INO_OWNER_EMAIL=you@example.com
CAF_INO_BOOTSTRAP_OWNER_PASSWORD=a-strong-password
```

Then run the deploy script again. The bootstrap command is idempotent for the matching owner/business.

## Update

```bash
git pull --ff-only origin main
./deploy/vps/deploy.sh YOUR_DOMAIN YOUR_EMAIL
```

## Verify

```bash
curl -fsS https://YOUR_DOMAIN/api/v1/health/
curl -I https://YOUR_DOMAIN/login
docker compose --env-file deploy/vps/.env.vps -f deploy/vps/compose.prod.yml ps
```

Do not expose ports 9860/9861 publicly; Nginx is the public entry point.
