# Cafino native VPS deployment

Cafino production on this VPS is intentionally **container-free**.

## Runtime

- Next.js: `cafino-frontend.service` on `127.0.0.1:9861`
- Django/Gunicorn: `cafino-backend.service` on `127.0.0.1:9860`
- Celery Worker: `cafino-worker.service`
- Celery Beat: `cafino-beat.service`
- PostgreSQL: host service
- Redis: host service
- Nginx: public reverse proxy
- Public hostname: `cafeno.digitalafarin.ir`

No Docker or Docker Compose is required.

## First install

Create the backend environment file first:

```bash
sudo install -d -m 0750 /etc/cafino
sudo cp deploy/vps/backend.env.example /etc/cafino/backend.env
sudo nano /etc/cafino/backend.env
sudo chmod 0640 /etc/cafino/backend.env
```

The existing production PostgreSQL database should be referenced by `DATABASE_URL`; do not create a replacement database during a migration of an existing live deployment.

Then:

```bash
chmod +x deploy/vps/install-native.sh deploy/vps/update.sh
./deploy/vps/install-native.sh
```

## Routine update

```bash
cd /path/to/coffino
./deploy/vps/update.sh
```

The update performs a fast-forward pull, Python dependency install, migrations, collectstatic, `npm ci`, Next.js build, controlled service restarts, and local health verification.

## DigitalAfarin Platform

The four `cafino-*.service` units are intentionally ordinary systemd services so they can be discovered/adopted by DigitalAfarin Platform without introducing a container runtime.
