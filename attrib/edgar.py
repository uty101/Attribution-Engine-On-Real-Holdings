"""EDGAR HTTP client and the 13F and N-PORT parsers (kickoff Section 5.1).

Only `scripts/pull_data.py` constructs an `EdgarClient` (rule 8); tests drive it
with a fake session object.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

import requests


class EdgarClient:
    """Rate-limited GET with retries on HTTP 429 and 5xx.

    A request counts towards `min_interval` when it is sent, not when it returns.
    """

    def __init__(
        self,
        user_agent: str,
        min_interval: float,
        retries: int,
        backoff: Sequence[float],
        session=None,
    ) -> None:
        if len(backoff) != retries:
            raise ValueError(f"len(backoff) = {len(backoff)} must equal retries = {retries}")
        self.user_agent = user_agent
        self.min_interval = min_interval
        self.retries = retries
        self.backoff = list(backoff)
        self.session = session if session is not None else requests.Session()
        self._last_sent: float | None = None

    def _send(self, url: str):
        if self._last_sent is not None:
            wait = self.min_interval - (time.monotonic() - self._last_sent)
            if wait > 0:
                time.sleep(wait)
        self._last_sent = time.monotonic()
        return self.session.get(url, headers={"User-Agent": self.user_agent})

    def _get(self, url: str):
        for attempt in range(self.retries + 1):
            resp = self._send(url)
            status = resp.status_code
            if status == 200:
                return resp
            if status != 429 and not 500 <= status <= 599:
                raise RuntimeError(f"HTTP {status} for {url}")
            if attempt == self.retries:
                raise RuntimeError(f"HTTP {status} for {url} after {self.retries} retries")
            time.sleep(self.backoff[attempt])
        raise AssertionError("unreachable")

    def get_json(self, url: str) -> dict:
        return self._get(url).json()

    def get_bytes(self, url: str) -> bytes:
        return self._get(url).content
