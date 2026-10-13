"""Section 56/87: rate limiting is disabled by default in this dev/test
environment (see app/core/config.py::rate_limit_enabled), but the
mechanism itself must be verified, not just wired and left untested. This
test forces the shared middleware's settings on with a tiny limit and
confirms real 429s, then restores the disabled default so later tests
(which share the module-level `app.main.app`/`limiter` state) are
unaffected."""

from app.core import rate_limit as rate_limit_module


def test_rate_limit_returns_429_once_exceeded(client, monkeypatch):
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_enabled", True)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_default", "3/minute")

    statuses = [client.get("/api/v1/health").status_code for _ in range(5)]

    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses


def test_rate_limit_is_a_noop_when_disabled(client):
    # Default test-session settings: rate_limit_enabled=False.
    statuses = [client.get("/api/v1/health").status_code for _ in range(10)]
    assert all(s == 200 for s in statuses)
