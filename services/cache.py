"""
cache.py — small in-process TTL cache.

The original site served its public pages with Next.js ISR (`revalidate = 300`)
and called `revalidatePath()` after every admin write. This is the equivalent:
public reads go through `cache`, and every successful write calls `clear()`.

The cache is per worker process. On Posit Connect with more than one process per
content item, another process may serve data up to CACHE_TTL_SECONDS old —
exactly the window the original ISR had.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

import constants as C


class TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            hit = self._data.get(key)
            if hit and hit[0] > time.monotonic():
                return hit[1]
            if hit:
                del self._data[key]
        return None

    def put(self, key: str, value: Any) -> None:
        if self._ttl <= 0:
            return
        with self._lock:
            self._data[key] = (time.monotonic() + self._ttl, value)

    def get_or_load(self, key: str, loader: Callable[[], Any]) -> Any:
        """Return the cached value or call `loader()` (an exception is never cached)."""
        value = self.get(key)
        if value is not None:
            return value
        value = loader()
        self.put(key, value)
        return value

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


cache = TTLCache(C.CACHE_TTL_SECONDS)
