from __future__ import annotations

import hmac
import json
from collections.abc import Awaitable, Callable


INTERNAL_SERVICE_TOKEN_HEADER = b"x-internal-service-token"
MINIMUM_TOKEN_LENGTH = 32
FORBIDDEN_TOKEN_VALUES = {
    "changeme",
    "change-me",
    "placeholder",
    "secret",
    "your-token-here",
}
PUBLIC_PATHS = {
    "/",
    "/health",
    "/health/live",
    "/health/ready",
    "/health/dependencies",
    "/metrics",
}


def is_valid_internal_token(value: str) -> bool:
    normalized = (value or "").strip()
    return len(normalized) >= MINIMUM_TOKEN_LENGTH and normalized.lower() not in FORBIDDEN_TOKEN_VALUES


def require_valid_internal_token_configuration(value: str) -> str:
    normalized = (value or "").strip()
    if not is_valid_internal_token(normalized):
        raise RuntimeError("internal service authentication is missing or invalid")
    return normalized


class InternalServiceAuthMiddleware:
    """Rejects direct access to Python business routes before routing occurs."""

    def __init__(self, app, token: str):
        self.app = app
        self.token = (token or "").strip()

    async def __call__(self, scope, receive, send) -> None:
        scope_type = scope.get("type")
        if scope_type not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")
        if path in PUBLIC_PATHS or method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        supplied = [
            value.decode("utf-8", errors="replace").strip()
            for key, value in scope.get("headers", [])
            if key.lower() == INTERNAL_SERVICE_TOKEN_HEADER
        ]
        configured = is_valid_internal_token(self.token)
        authenticated = (
            configured
            and len(supplied) == 1
            and bool(supplied[0])
            and hmac.compare_digest(supplied[0], self.token)
        )
        if authenticated:
            await self.app(scope, receive, send)
            return

        if scope_type == "websocket":
            await send({"type": "websocket.close", "code": 4403, "reason": "access denied"})
            return

        status = 401 if configured and not supplied else 403
        body = json.dumps({"detail": "access denied"}, separators=(",", ":")).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
