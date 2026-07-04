"""In-memory GPS fix storage."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from threading import Lock


@dataclass
class LocationFix:
    lat: float
    lng: float
    accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None
    altitude: float | None = None
    device_id: str = "phone"
    received_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


class LocationStore:
    def __init__(self, *, history_size: int = 120) -> None:
        self._lock = Lock()
        self._latest: LocationFix | None = None
        self._history: list[LocationFix] = []
        self._history_size = max(10, history_size)
        self._session_started_at: float | None = None

    def update(self, fix: LocationFix) -> LocationFix:
        with self._lock:
            if self._session_started_at is None:
                self._session_started_at = time.time()
            self._latest = fix
            self._history.append(fix)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size :]
            return fix

    def latest(self) -> LocationFix | None:
        with self._lock:
            return self._latest

    def history(self, limit: int = 50) -> list[dict]:
        with self._lock:
            items = self._history[-limit:]
            return [item.to_dict() for item in items]

    def status(self) -> dict:
        with self._lock:
            latest = self._latest
            now = time.time()
            age_sec = None if latest is None else round(now - latest.received_at, 2)
            return {
                "live": latest is not None and age_sec is not None and age_sec < 15,
                "fix_count": len(self._history),
                "session_started_at": self._session_started_at,
                "last_fix_age_sec": age_sec,
                "latest": latest.to_dict() if latest else None,
            }

    def clear(self) -> None:
        with self._lock:
            self._latest = None
            self._history.clear()
            self._session_started_at = None
