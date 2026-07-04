# API reference

Base URL: your deployment host (e.g. `https://gps.example.com`).

Unless noted, read endpoints require `ACCESS_PASSWORD` when that env var is set. See [auth.md](auth.md).

## Health

### `GET /health`

Public. Used by Docker health checks.

```json
{
  "status": "ok",
  "live": true,
  "fix_count": 42,
  "session_started_at": 1717512000.0,
  "last_fix_age_sec": 1.23,
  "latest": { "...": "..." }
}
```

## Location

### `GET /api/location`

Latest GPS fix.

**Response (fix available)**

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

**Response (no fix yet)**

```json
{
  "ok": false,
  "location": null,
  "message": "No GPS fix yet — open / on your phone."
}
```

### `POST /api/location`

Accept a new fix from the phone or a script. Protected by `GPS_TOKEN` when configured (not by `ACCESS_PASSWORD`).

**Headers**

| Header | Description |
|--------|-------------|
| `Content-Type` | `application/json` |
| `X-GPS-Token` | Token matching `GPS_TOKEN` |
| `Authorization` | `Bearer <GPS_TOKEN>` (alternative) |

**Body**

```json
{
  "lat": 53.8659,
  "lng": 10.6866,
  "accuracy": 8.5,
  "heading": 180.0,
  "speed": 1.2,
  "altitude": 12.0,
  "device_id": "phone",
  "client_time": 1717512345.67
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `lat` | float | yes | -90 … 90 |
| `lng` | float | yes | -180 … 180 |
| `accuracy` | float | no | ≥ 0 |
| `heading` | float | no | degrees |
| `speed` | float | no | ≥ 0 m/s |
| `altitude` | float | no | meters |
| `device_id` | string | no | default `"phone"` |
| `client_time` | float | no | Unix timestamp from client |

**Response**

```json
{
  "ok": true,
  "location": { "...": "..." }
}
```

Broadcasts a WebSocket message to all connected dashboard clients.

### `GET /api/location/history?limit=50`

Recent fixes, newest last. `limit` is clamped to 1–500.

```json
{
  "ok": true,
  "history": [
    { "lat": 53.865, "lng": 10.686, "...": "..." }
  ],
  "status": { "...": "..." }
}
```

### `POST /api/location/clear`

Clears in-memory session. Requires `GPS_TOKEN` when configured.

```json
{
  "ok": true,
  "message": "GPS session cleared"
}
```

## Status

### `GET /api/status`

Session summary without wrapping the location in a separate key.

```json
{
  "ok": true,
  "live": true,
  "fix_count": 42,
  "session_started_at": 1717512000.0,
  "last_fix_age_sec": 1.23,
  "latest": { "...": "..." }
}
```

`live` is `true` when the most recent fix is less than **15 seconds** old.

## WebSocket

### `WS /ws`

Live stream for the dashboard. Requires `ACCESS_PASSWORD` when configured.

**Auth** — same as HTTP read endpoints:

- Browser: automatic after HTTP Basic login on `/dashboard`
- Scripts: `Authorization: Bearer <ACCESS_PASSWORD>` on the upgrade request

**Messages (server → client)**

Location update:

```json
{
  "type": "location",
  "lat": 53.8659,
  "lng": 10.6866,
  "accuracy": 8.5,
  "heading": 180.0,
  "speed": 1.2,
  "altitude": 12.0,
  "device_id": "phone",
  "received_at": 1717512345.67
}
```

Status snapshot:

```json
{
  "type": "status",
  "live": true,
  "fix_count": 42,
  "session_started_at": 1717512000.0,
  "last_fix_age_sec": 1.23,
  "latest": { "...": "..." }
}
```

On connect, the server sends the latest fix (if any) then a status message. Clients may send text frames to keep the connection open; payloads are ignored.

## Pages

| Route | Redirects to | Auth |
|-------|--------------|------|
| `/` | `/static/phone.html` | Public |
| `/dashboard` | `/static/dashboard.html` | `ACCESS_PASSWORD` |

Static assets under `/static/` are public except `/static/dashboard.html`.
