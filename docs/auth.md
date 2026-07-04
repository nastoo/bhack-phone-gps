# Authentication

The service uses two optional secrets. Both can be unset for fully open local development.

## Overview

| Secret | Protects | Used by |
|--------|----------|---------|
| `ACCESS_PASSWORD` | Dashboard, read API, WebSocket | Operators and integrating services |
| `GPS_TOKEN` | POST location and clear session | Phone page and scripts sending GPS |

This split lets walkers open the phone page without a login, while viewers and API consumers need a password. Posting fake GPS data requires knowing `GPS_TOKEN`.

## ACCESS_PASSWORD

Set in `.env`:

```env
ACCESS_PASSWORD=choose-a-strong-password
```

### Protected when set

- `/dashboard` and `/static/dashboard.html`
- `GET /api/location`
- `GET /api/location/history`
- `GET /api/status`
- `WebSocket /ws`

### Always public

- `/` and `/static/phone.html`
- `/health`
- `/static/styles.css`
- `POST /api/location` and `POST /api/location/clear` (use `GPS_TOKEN` instead)

### Browser (dashboard)

Open `/dashboard`. The browser prompts for credentials:

- **Username** — anything (ignored)
- **Password** — value of `ACCESS_PASSWORD`

After login, `fetch` and WebSocket calls on the same origin reuse the session automatically.

### HTTP clients

Any of these work:

**HTTP Basic Auth** (password only matters):

```bash
curl -u "viewer:$ACCESS_PASSWORD" https://host/api/location
```

**Bearer token:**

```bash
curl -H "Authorization: Bearer $ACCESS_PASSWORD" https://host/api/location
```

**Custom header:**

```bash
curl -H "X-Access-Token: $ACCESS_PASSWORD" https://host/api/status
```

### WebSocket (non-browser)

Pass `Authorization: Bearer <ACCESS_PASSWORD>` on the WebSocket upgrade request.

## GPS_TOKEN

Set in `.env`:

```env
GPS_TOKEN=demo-secret
```

When set, these endpoints reject requests without a valid token:

- `POST /api/location`
- `POST /api/location/clear`

### Phone page

Enter the token in **Optional token** on `/` before tapping **Start sharing**.

### HTTP clients

```bash
curl -X POST https://host/api/location \
  -H "Content-Type: application/json" \
  -H "X-GPS-Token: $GPS_TOKEN" \
  -d '{"lat": 53.86, "lng": 10.68}'
```

Or:

```bash
-H "Authorization: Bearer $GPS_TOKEN"
```

When `GPS_TOKEN` is **not** set, anyone can POST location updates.

## Recommended production setup

```env
ACCESS_PASSWORD=long-random-viewer-password
GPS_TOKEN=long-random-poster-token
```

Use different values for each secret. Store them in:

- Local `.env` (never commit — already in `.gitignore`)
- GitHub Actions environment secrets for deploy (`ACCESS_PASSWORD`, `GPS_TOKEN`)

## GitHub Actions secrets

In the repo **Settings → Environments → prod**:

| Type | Name | Purpose |
|------|------|---------|
| Secret | `ACCESS_PASSWORD` | Dashboard / read API auth |
| Secret | `GPS_TOKEN` | Location POST auth |
| Secret | `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT` | Deploy SSH |
| Variable | `TRAEFIK_HOST` | Public hostname |
| Variable | `CERT_RESOLVER` | Traefik cert resolver (optional) |
| Variable | `GPS_HISTORY_SIZE` | History buffer size (optional) |

The deploy workflow writes these into `.env` on the server before `docker compose up`.
