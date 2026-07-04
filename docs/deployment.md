# Deployment

Phone GPS Stream runs as a single Docker container behind [Traefik](https://doc.traefik.io/traefik/) for HTTPS.

## Prerequisites

- Docker and Docker Compose on the server
- Traefik already running with an external network named `traefik_proxy`
- DNS `A`/`AAAA` record pointing to the server
- Traefik certificate resolver configured (e.g. Let's Encrypt)

## Environment file

On the server, create `.env` next to `docker-compose.yml` (or let CI generate it):

```env
TRAEFIK_HOST=gps.example.com
CERT_RESOLVER=letsencrypt
ACCESS_PASSWORD=your-viewer-password
GPS_TOKEN=your-poster-token
GPS_HISTORY_SIZE=120
```

`TRAEFIK_HOST` must match **exactly** what you type in the browser.

## Docker Compose

```bash
docker compose up -d --build
```

The compose file:

- Builds the app image from `Dockerfile`
- Attaches to external network `traefik_proxy`
- Registers Traefik routes for HTTPS on `TRAEFIK_HOST`
- Exposes port **8080** inside the container (Traefik proxies to it)
- Runs a health check on `GET /health`

Verify:

```bash
docker compose ps
docker compose logs -f gps-stream
curl -s https://gps.example.com/health
```

## Local development (without Traefik)

Run uvicorn directly:

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Or build and run the container alone (no Traefik labels needed):

```bash
docker build -t phone-gps .
docker run --rm -p 8080:8080 --env-file .env phone-gps
```

Open http://localhost:8080/

## Traefik labels

Defined in `docker-compose.yml`:

| Label | Purpose |
|-------|---------|
| `traefik.enable=true` | Enable routing for this container |
| `traefik.http.routers.phone-gps.rule=Host(...)` | Route by hostname |
| `traefik.http.routers.phone-gps.entrypoints=websecure` | HTTPS entrypoint |
| `traefik.http.routers.phone-gps.tls=true` | Enable TLS |
| `traefik.http.routers.phone-gps.tls.certresolver=...` | Certificate resolver from `.env` |
| `traefik.http.services.phone-gps.loadbalancer.server.port=8080` | Backend port |

Ensure your Traefik static config defines the same `certresolver` name as `CERT_RESOLVER` in `.env`.

## GitHub Actions deploy

Pushes to `master` (and manual **workflow_dispatch**) trigger `.github/workflows/deploy.yml`.

Flow:

1. SSH to the server and ensure deploy directory exists (`/home/nathan/phone_gps` by default)
2. Copy project files via SCP
3. Write `.env` from GitHub environment vars/secrets
4. Run `docker compose up -d --build --remove-orphans`

### Required GitHub configuration

**Environment:** `prod`

**Secrets**

- `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT`
- `GPS_TOKEN`
- `ACCESS_PASSWORD`

**Variables**

- `TRAEFIK_HOST` (required)
- `CERT_RESOLVER` (optional, default `letsencrypt`)
- `GPS_HISTORY_SIZE` (optional, default `120`)

### Manual deploy on the server

If you skip CI, copy the repo to the server and run:

```bash
cd /path/to/phone_gps
cp .env.example .env   # edit values
docker compose up -d --build
```

## Upgrading

```bash
cd /path/to/phone_gps
git pull   # or re-run the GitHub Action
docker compose up -d --build
```

In-memory GPS data is lost on container restart.

## Monitoring

- **Health:** `GET /health` — returns `{"status": "ok", ...}`
- **Docker:** `docker compose ps` — health column should show `healthy`
- **Logs:** `docker compose logs -f gps-stream`
