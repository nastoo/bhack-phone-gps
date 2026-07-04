"""Phone GPS stream — lightweight service for demo navigation."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import access_required, is_authorized, unauthorized_response
from app.store import LocationFix, LocationStore

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
GPS_TOKEN = os.environ.get("GPS_TOKEN", "").strip()
HISTORY_SIZE = int(os.environ.get("GPS_HISTORY_SIZE", "120"))

store = LocationStore(history_size=HISTORY_SIZE)
_ws_clients: set[WebSocket] = set()

app = FastAPI(title="Phone GPS Stream", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccessAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if access_required(path, request.method) and not is_authorized(request):
            return unauthorized_response()
        return await call_next(request)


app.add_middleware(AccessAuthMiddleware)


class LocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)
    heading: float | None = None
    speed: float | None = Field(default=None, ge=0)
    altitude: float | None = None
    device_id: str = "phone"
    client_time: float | None = None


def _check_token(authorization: str | None, x_gps_token: str | None) -> None:
    if not GPS_TOKEN:
        return
    token = (x_gps_token or "").strip()
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token != GPS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid GPS token")


async def _broadcast(fix: LocationFix) -> None:
    if not _ws_clients:
        return
    message = json.dumps({"type": "location", **fix.to_dict()})
    dead: list[WebSocket] = []
    for ws in list(_ws_clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


@app.get("/health")
def health():
    return {"status": "ok", **store.status()}


@app.get("/")
def index():
    return RedirectResponse(url="/static/phone.html")


@app.get("/dashboard")
def dashboard():
    return RedirectResponse(url="/static/dashboard.html")


@app.get("/api/location")
def get_location():
    fix = store.latest()
    if fix is None:
        return {"ok": False, "location": None, "message": "No GPS fix yet — open / on your phone."}
    return {"ok": True, "location": fix.to_dict(), "status": store.status()}


@app.get("/api/location/history")
def get_history(limit: int = 50):
    limit = max(1, min(limit, 500))
    return {"ok": True, "history": store.history(limit), "status": store.status()}


@app.get("/api/status")
def get_status():
    return {"ok": True, **store.status()}


@app.post("/api/location")
async def post_location(
    body: LocationUpdate,
    authorization: str | None = Header(default=None),
    x_gps_token: str | None = Header(default=None),
):
    _check_token(authorization, x_gps_token)
    fix = LocationFix(
        lat=body.lat,
        lng=body.lng,
        accuracy=body.accuracy,
        heading=body.heading,
        speed=body.speed,
        altitude=body.altitude,
        device_id=body.device_id or "phone",
        received_at=time.time(),
    )
    store.update(fix)
    await _broadcast(fix)
    return {"ok": True, "location": fix.to_dict()}


@app.post("/api/location/clear")
def clear_location(
    authorization: str | None = Header(default=None),
    x_gps_token: str | None = Header(default=None),
):
    _check_token(authorization, x_gps_token)
    store.clear()
    return {"ok": True, "message": "GPS session cleared"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if access_required("/ws", "GET") and not is_authorized(websocket):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        latest = store.latest()
        if latest is not None:
            await websocket.send_text(json.dumps({"type": "location", **latest.to_dict()}))
        await websocket.send_text(json.dumps({"type": "status", **store.status()}))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
