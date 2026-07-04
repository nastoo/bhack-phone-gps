"""Optional password gate for dashboard and read-only GPS endpoints."""

from __future__ import annotations

import base64
import binascii
import os
import secrets

from starlette.requests import Request
from starlette.responses import Response

ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "").strip()
AUTH_REALM = "GPS Dashboard"

# Phone page and health stay public; posting uses GPS_TOKEN in route handlers.
_PUBLIC_PATHS = frozenset(
    {
        "/",
        "/health",
        "/static/phone.html",
        "/static/styles.css",
    }
)


def access_required(path: str, method: str) -> bool:
    if not ACCESS_PASSWORD:
        return False
    if path in _PUBLIC_PATHS:
        return False
    if path.startswith("/static/") and path != "/static/dashboard.html":
        return False
    if path == "/api/location" and method == "POST":
        return False
    if path == "/api/location/clear" and method == "POST":
        return False
    return True


def is_authorized(request: Request) -> bool:
    if not ACCESS_PASSWORD:
        return True

    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(auth[6:].strip()).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False
        _, _, password = decoded.partition(":")
        return secrets.compare_digest(password, ACCESS_PASSWORD)

    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        return secrets.compare_digest(token, ACCESS_PASSWORD)

    header_token = request.headers.get("x-access-token", "").strip()
    if header_token:
        return secrets.compare_digest(header_token, ACCESS_PASSWORD)

    return False


def unauthorized_response() -> Response:
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": f'Basic realm="{AUTH_REALM}"'},
        content="Authentication required",
        media_type="text/plain",
    )
