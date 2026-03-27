"""Tests for backend/app/services/cezih/oauth.py — OAuth2 token management."""

import time
from unittest.mock import AsyncMock, patch

import pytest

import app.services.cezih.oauth as oauth_mod
from app.services.cezih.oauth import _is_token_valid, get_oauth_token, invalidate_token

_MONOTONIC_NOW = 1000.0


def _reset_oauth_cache():
    oauth_mod._token_cache = None
    oauth_mod._token_acquired_at = 0.0


class TestIsTokenValid:
    def setup_method(self):
        _reset_oauth_cache()

    def teardown_method(self):
        _reset_oauth_cache()

    def test_no_cache(self):
        assert _is_token_valid() is False

    @patch("app.services.cezih.oauth.time.monotonic", return_value=1000.0)
    def test_valid(self, mock_time):
        oauth_mod._token_cache = type("T", (), {"access_token": "tok", "expires_in": 300})()
        oauth_mod._token_acquired_at = 800.0  # 200s ago, within 270s buffer
        assert _is_token_valid() is True

    @patch("app.services.cezih.oauth.time.monotonic", return_value=1000.0)
    def test_expired(self, mock_time):
        oauth_mod._token_cache = type("T", (), {"access_token": "tok", "expires_in": 300})()
        oauth_mod._token_acquired_at = 700.0  # 300s ago, exceeds 270s buffer
        assert _is_token_valid() is False


class TestGetOAuthToken:
    @pytest.mark.asyncio
    @patch("app.services.cezih.oauth.time.monotonic", return_value=1000.0)
    async def test_cached_token(self, mock_time):
        """When token is valid, client.post should NOT be called."""
        oauth_mod._token_cache = type("T", (), {"access_token": "cached-tok", "expires_in": 300})()
        oauth_mod._token_acquired_at = 800.0  # 200s ago, within 270s buffer

        mock_client = AsyncMock()
        token = await get_oauth_token(client=mock_client)
        assert token == "cached-tok"
        mock_client.post.assert_not_called()
        _reset_oauth_cache()

    @pytest.mark.asyncio
    @patch("app.services.cezih.oauth.time.monotonic", return_value=1000.0)
    @patch.object(oauth_mod, "settings")
    async def test_fetch_new_token(self, mock_settings, mock_time):
        mock_settings.CEZIH_OAUTH2_URL = "https://example.com/token"
        mock_settings.CEZIH_CLIENT_ID = "test-id"
        mock_settings.CEZIH_CLIENT_SECRET = "test-secret"
        mock_settings.CEZIH_TIMEOUT = 10

        _reset_oauth_cache()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = '{"access_token":"new-tok","expires_in":300}'
        mock_response.raise_for_status = lambda: None  # sync method

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        token = await get_oauth_token(client=mock_client)
        assert token == "new-tok"
        mock_client.post.assert_called_once()
        _reset_oauth_cache()


class TestInvalidateToken:
    def test_sets_cache_to_none(self):
        oauth_mod._token_cache = "something"
        oauth_mod._token_acquired_at = 999.0
        invalidate_token()
        assert oauth_mod._token_cache is None
        assert oauth_mod._token_acquired_at == 0.0
