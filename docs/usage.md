# Usage guide

This walkthrough covers the day-to-day use of Phone GPS Stream during a demo or hackathon.

## Roles

| Role | What they do | URL |
|------|--------------|-----|
| Walker | Carries the phone and streams GPS | `/` |
| Operator | Watches the map on a laptop | `/dashboard` |
| Integration | Another service reads position | `/api/location` |

## Phone page (walker)

1. Open the root URL on the phone (e.g. `https://gps.example.com/`).
2. If your deployment uses `GPS_TOKEN`, paste the token into **Optional token** before starting.
3. Tap **Start sharing** and allow location when the browser asks.
4. Keep the page open and the screen awake while walking. Updates are sent about every 2 seconds.
5. Tap **Stop** when the demo is over.

**Tips**

- Use **high accuracy** mode — the page requests `enableHighAccuracy: true`.
- Safari on iOS may pause background tabs; keep the phone unlocked if possible.
- The status line shows live accuracy (e.g. `±12 m`) when streaming works.
- If you see `Send failed: Invalid GPS token`, check the token matches `GPS_TOKEN` in `.env`.

The phone page does **not** require `ACCESS_PASSWORD`. Only posting location can be locked down with `GPS_TOKEN`.

## Dashboard (operator)

1. Open `/dashboard` in a desktop browser.
2. If `ACCESS_PASSWORD` is set, the browser shows a login prompt. Enter any username and the password from `.env`.
3. The map centers on the latest fix and draws a blue trail as new points arrive.
4. Status shows **Live** when the last fix is less than 15 seconds old.

The dashboard uses:

- **WebSocket** (`/ws`) for instant updates
- **Polling** (`/api/status` every 3 s) as a fallback

Use the **Open phone page** link in the header to get the sharing URL for the walker.

## Integrating another service

The dashboard footer shows a copy-paste snippet. For a guide or navigation backend, set:

```bash
GPS_STREAM_URL=https://your-host.example.com
```

Then poll the latest fix:

```bash
curl -u ":$ACCESS_PASSWORD" \
  https://your-host.example.com/api/location
```

Or with a bearer token:

```bash
curl -H "Authorization: Bearer $ACCESS_PASSWORD" \
  https://your-host.example.com/api/location
```

Example response when a fix exists:

```json
{
  "ok": true,
  "location": {
    "lat": 53.8659,
    "lng": 10.6866,
    "accuracy": 8.5,
    "heading": 180.0,
    "speed": 1.2,
    "altitude": 12.0,
    "device_id": "phone",
    "received_at": 1717512345.67
  },
  "status": { "...": "..." }
}
```

When nobody is sharing yet:

```json
{
  "ok": false,
  "location": null,
  "message": "No GPS fix yet — open / on your phone."
}
```

See [api.md](api.md) for all endpoints.

## Clearing a session

To reset stored fixes (e.g. between demos):

```bash
curl -X POST \
  -H "X-GPS-Token: $GPS_TOKEN" \
  https://your-host.example.com/api/location/clear
```

Requires `GPS_TOKEN` when that variable is configured.

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Dashboard shows "Waiting…" / no marker | Phone page not started, or walker denied location permission |
| Dashboard 401 | Wrong or missing `ACCESS_PASSWORD` |
| Phone "Send failed" | Wrong `GPS_TOKEN`, or server unreachable |
| Status "Stale / offline" | No fix in the last 15 seconds — check phone connection |
| Map works locally but not in prod | `TRAEFIK_HOST` must match the URL in the browser exactly |

Health check (always public): `GET /health`
