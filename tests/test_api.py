import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import ConflictError, AuthenticationError, NotFoundError

client = TestClient(app)

# ----------------------------------------------------
# AUTHENTICATION ROUTE TESTS
# ----------------------------------------------------

def test_signup_validation_error():
    # Passwords must be at least 8 characters
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "invalid-email", "password": "short"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_signup_success():
    mock_user = AsyncMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test@example.com"
    mock_user.created_at = datetime.now(timezone.utc)

    with patch("app.api.v1.auth.create_user", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_user
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "test@example.com", "password": "securepassword123"}
        )
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"
        assert "id" in response.json()


def test_signup_conflict():
    with patch("app.api.v1.auth.create_user", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = ConflictError("A user with this email already exists")
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "test@example.com", "password": "securepassword123"}
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "A user with this email already exists"


def test_login_success():
    mock_user = AsyncMock()
    mock_user.email = "test@example.com"
    
    with patch("app.api.v1.auth.authenticate_user", new_callable=AsyncMock) as mock_auth, \
         patch("app.api.v1.auth.create_access_token") as mock_token:
        mock_auth.return_value = mock_user
        mock_token.return_value = "mocked-jwt-token"
        
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "securepassword123"}
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "mocked-jwt-token"
        assert response.json()["token_type"] == "bearer"


def test_login_failure():
    with patch("app.api.v1.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.side_effect = AuthenticationError("Incorrect email or password")
        
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"


# ----------------------------------------------------
# URL SHORTENING ROUTE TESTS
# ----------------------------------------------------

def test_shorten_url_validation_error():
    # Invalid target URL
    response = client.post(
        "/api/v1/urls/",
        json={"original_url": "not-a-valid-url"}
    )
    assert response.status_code == 422


def test_shorten_url_success_anonymous():
    mock_url = AsyncMock()
    mock_url.id = 1001
    mock_url.original_url = "https://google.com"
    mock_url.short_code = "gb"
    mock_url.expires_at = None
    mock_url.created_at = datetime.now(timezone.utc)
    mock_url.user_id = None

    with patch("app.api.v1.urls.url_service.create_short_url", new_callable=AsyncMock) as mock_create, \
         patch("app.core.limiter.RateLimiter.__call__", new_callable=AsyncMock):
        mock_create.return_value = mock_url
        
        response = client.post(
            "/api/v1/urls/",
            json={"original_url": "https://google.com"}
        )
        assert response.status_code == 201
        res_data = response.json()
        assert res_data["short_code"] == "gb"
        assert "http://testserver/gb" in res_data["short_url"]
        assert res_data["user_id"] is None


def test_shorten_url_custom_alias_taken():
    with patch("app.api.v1.urls.url_service.create_short_url", new_callable=AsyncMock) as mock_create, \
         patch("app.core.limiter.RateLimiter.__call__", new_callable=AsyncMock):
        mock_create.side_effect = ConflictError("Custom alias is already in use")
        
        response = client.post(
            "/api/v1/urls/",
            json={"original_url": "https://google.com", "custom_alias": "goog"}
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Custom alias is already in use"


# ----------------------------------------------------
# REDIRECT AND ANALYTICS TESTS
# ----------------------------------------------------

def test_redirect_not_found():
    with patch("app.main.url_service.resolve_url", new_callable=AsyncMock) as mock_resolve, \
         patch("app.core.limiter.RateLimiter.__call__", new_callable=AsyncMock):
        mock_resolve.side_effect = NotFoundError("Short URL not found")
        
        response = client.get("/nonexistent", follow_redirects=False)
        assert response.status_code == 404
        assert response.json()["detail"] == "Short URL not found"


def test_redirect_success():
    mock_url = AsyncMock()
    mock_url.id = 1001
    mock_url.original_url = "https://google.com"
    mock_url.short_code = "gb"

    with patch("app.main.url_service.resolve_url", new_callable=AsyncMock) as mock_resolve, \
         patch("app.main.analytics_service.record_click") as mock_record, \
         patch("app.core.limiter.RateLimiter.__call__", new_callable=AsyncMock):
        mock_resolve.return_value = mock_url
        
        response = client.get("/gb", follow_redirects=False)
        # Verify 307 Temporary Redirect code is used
        assert response.status_code == 307
        assert response.headers["location"] == "https://google.com"
