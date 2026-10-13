"""Rate limiting (Section 56/87), backed directly by the `limits` library
(an ASGI-framework-agnostic rate-limiting primitive) via a small ASGI
middleware, rather than the `slowapi` wrapper around it.

Why not slowapi: it was tried first, but its `SlowAPIMiddleware` silently
stopped enforcing limits under Starlette 1.x (root-caused during the
dependency-vulnerability upgrade pass - see `docs/security/dependency-audit.md`)
while returning no error, which is a worse failure mode than not having
rate limiting at all - a security control that looks wired but silently
does nothing. `limits` itself has no Starlette/FastAPI-version coupling
(it operates purely on a caller-supplied string key), so this middleware
depends on nothing but the stable ASGI three-argument callable interface.

Disabled by default in this environment's `.env` (see
`app/core/config.py::rate_limit_enabled`'s docstring for why) - production
deployments should set `RATE_LIMIT_ENABLED=true`.
"""

from limits import RateLimitItem, parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings

settings = get_settings()

_storage = MemoryStorage()
_strategy = MovingWindowRateLimiter(_storage)

# Stricter limit for the two auth endpoints (brute-force protection);
# every other path gets the general default limit.
_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}


def _default_rate() -> RateLimitItem:
    return parse(settings.rate_limit_default)


def _auth_rate() -> RateLimitItem:
    return parse(settings.rate_limit_auth)


def _client_key(scope: Scope) -> str:
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Real per-client-IP rate limiting. A no-op (settings.rate_limit_enabled
    is re-read on every request, not cached at import time, so tests can
    flip it via monkeypatching an already-constructed app)."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not settings.rate_limit_enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        is_auth = path in _AUTH_PATHS
        rate = _auth_rate() if is_auth else _default_rate()
        key = f"{_client_key(scope)}:{'auth' if is_auth else 'default'}"

        if not _strategy.hit(rate, key):
            response = JSONResponse(
                {"detail": f"Rate limit exceeded: {settings.rate_limit_auth if is_auth else settings.rate_limit_default}"},
                status_code=429,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
