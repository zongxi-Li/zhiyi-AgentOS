from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security.internal_auth import (
    INTERNAL_SERVICE_TOKEN_HEADER,
    InternalServiceAuthMiddleware,
    require_valid_internal_token_configuration,
)


TOKEN = "0123456789abcdef0123456789abcdef"
HEADER = INTERNAL_SERVICE_TOKEN_HEADER.decode("ascii")


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(InternalServiceAuthMiddleware, token=TOKEN)

    @app.get("/health/live")
    async def live():
        return {"status": "UP"}

    @app.post("/ai/chat/text")
    async def business():
        return {"ok": True}

    return TestClient(app)


def test_correct_token_allows_business_route():
    response = _client().post("/ai/chat/text", headers={HEADER: TOKEN})
    assert response.status_code == 200


def test_missing_wrong_empty_and_duplicate_tokens_are_rejected():
    client = _client()
    assert client.post("/ai/chat/text").status_code == 401
    assert client.post("/ai/chat/text", headers={HEADER: "x" * 32}).status_code == 403
    assert client.post("/ai/chat/text", headers={HEADER: ""}).status_code == 403
    duplicate = client.post("/ai/chat/text", headers=[(HEADER, TOKEN), (HEADER, TOKEN)])
    assert duplicate.status_code == 403
    assert duplicate.json() == {"detail": "access denied"}


def test_health_endpoint_does_not_require_internal_token():
    assert _client().get("/health/live").status_code == 200


def test_invalid_production_configuration_fails_without_echoing_value():
    try:
        require_valid_internal_token_configuration("too-short")
    except RuntimeError as error:
        assert str(error) == "internal service authentication is missing or invalid"
        assert "too-short" not in str(error)
    else:
        raise AssertionError("invalid token was accepted")
