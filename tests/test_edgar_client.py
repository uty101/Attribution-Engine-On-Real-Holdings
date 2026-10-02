import math
from pathlib import Path

import pytest
import requests

import attrib.edgar as edgar
from attrib.config import load_config
from attrib.edgar import EdgarClient

CFG = load_config(Path(__file__).resolve().parents[1] / "config.toml")
UA = "Test User <test@example.com>"


class FakeClock:
    """Stands in for the `time` module inside attrib.edgar."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.now += s


class FakeResponse:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}
        self.content = b"<xml/>"

    def json(self):
        return self._payload


class FakeSession:
    """`statuses` holds HTTP status codes, or exceptions to raise in place of a response."""

    def __init__(self, statuses: list):
        self.statuses = list(statuses)
        self.calls: list[tuple[str, dict]] = []
        self.timeouts: list = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, dict(headers or {})))
        self.timeouts.append(timeout)
        nxt = self.statuses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return FakeResponse(nxt)


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(edgar, "time", c)
    return c


def _client(session):
    e = CFG.edgar
    return EdgarClient(UA, e.min_interval_s, e.retries, e.backoff_s, e.timeout_s, session=session)


def test_user_agent_header_sent(clock):
    s = FakeSession([200])
    assert _client(s).get_json("https://data.sec.gov/x.json") == {"ok": True}
    assert s.calls == [("https://data.sec.gov/x.json", {"User-Agent": UA})]


def test_min_interval_respected(clock):
    s = FakeSession([200, 200, 200])
    c = _client(s)
    for _ in range(3):
        c.get_bytes("https://www.sec.gov/a")
    print("recorded sleeps:", clock.sleeps)
    assert len(clock.sleeps) == 2
    assert math.isclose(sum(clock.sleeps), 0.4, rel_tol=0, abs_tol=1e-9)


def test_429_then_200_retries_with_configured_waits(clock):
    s = FakeSession([429, 429, 200])
    _client(s).get_json("https://data.sec.gov/y.json")
    print("recorded sleeps:", clock.sleeps)
    assert clock.sleeps == [2, 4]
    assert len(s.calls) == 3


def test_three_failures_raise(clock):
    s = FakeSession([503, 503, 503, 503])
    with pytest.raises(RuntimeError, match="503"):
        _client(s).get_bytes("https://www.sec.gov/z")
    print("recorded sleeps:", clock.sleeps)
    assert clock.sleeps == [2, 4, 8]
    assert len(s.calls) == 4


def test_timeout_passed_to_get(clock):
    s = FakeSession([200])
    _client(s).get_bytes("https://www.sec.gov/t")
    print("recorded timeout:", s.timeouts)
    assert s.timeouts == [30]


def test_connection_error_then_200_retries(clock):
    s = FakeSession([requests.ConnectionError("reset by peer"), 200])
    assert _client(s).get_json("https://data.sec.gov/c.json") == {"ok": True}
    print("recorded sleeps:", clock.sleeps)
    assert clock.sleeps == [2]
    assert len(s.calls) == 2
