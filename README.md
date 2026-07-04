# Phone GPS Stream

A small FastAPI service that turns a phone into a live GPS beacon for demo navigation. One person walks with the phone page open; everyone else watches position on a map dashboard or polls the HTTP API.

## How it works

```
Phone (browser)          Server                 Consumers
     │                      │                        │
     │  POST /api/location  │                        │
     ├─────────────────────►│                        │
     │                      │  GET /api/location     │
     │                      │◄───────────────────────┤ guide / scripts
     │                      │                        │
     │                      │  WebSocket /ws         │
     │                      │◄───────────────────────┤ dashboard (live)
```

- **Phone page** (`/`) — uses the browser geolocation API and sends fixes every ~2 seconds.
- **Dashboard** (`/dashboard`) — Leaflet map with live updates over WebSocket.
- **REST API** — latest fix, history, and session status for other services.

Location data is stored in memory only (no database). Restarting the container clears the session.

## Quick start (local)

```bash
cp .env.example .env
# Edit .env — set ACCESS_PASSWORD and GPS_TOKEN for production use

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8080
```

| URL | Purpose |
|-----|---------|
| http://localhost:8080/ | Phone — share GPS |
| http://localhost:8080/dashboard | Map dashboard |
| http://localhost:8080/health | Health check |

## Typical demo workflow

1. Deploy the service (see [docs/deployment.md](docs/deployment.md)) or run it locally.
2. On the walker's phone, open **`/`**, tap **Start sharing**, and allow location access.
3. On a laptop, open **`/dashboard`** and sign in with `ACCESS_PASSWORD` when prompted.
4. Point your guide/navigation service at `GET /api/location` on the same host.

If `GPS_TOKEN` is set, the walker must enter it in the **Optional token** field on the phone page before sharing works.

## Configuration

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `TRAEFIK_HOST` | For production | Public hostname (must match DNS and browser URL) |
| `CERT_RESOLVER` | For production | Traefik certificate resolver name (default: `letsencrypt`) |
| `ACCESS_PASSWORD` | Recommended | Password for dashboard, read API, and WebSocket |
| `GPS_TOKEN` | Recommended | Secret required to **post** location updates |
| `GPS_HISTORY_SIZE` | No | Max fixes kept in memory (default: `120`) |

See [docs/auth.md](docs/auth.md) for details on what each secret protects.

## Documentation

- [Usage guide](docs/usage.md) — phone page, dashboard, integration tips
- [API reference](docs/api.md) — endpoints, payloads, WebSocket messages
- [Deployment](docs/deployment.md) — Docker, Traefik, GitHub Actions
- [Authentication](docs/auth.md) — passwords, tokens, and protected routes

## Project layout

```
phone_gps/
├── app/
│   ├── main.py      # FastAPI routes and WebSocket
│   ├── auth.py      # Optional ACCESS_PASSWORD gate
│   └── store.py     # In-memory location storage
├── static/
│   ├── phone.html   # GPS sharing UI
│   ├── dashboard.html
│   └── styles.css
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/deploy.yml
```

## License

Hackathon / internal demo project — use as needed for your team.
