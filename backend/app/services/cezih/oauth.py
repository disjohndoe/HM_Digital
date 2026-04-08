from __future__ import annotations

import asyncio
import logging
import time

import httpx

from app.config import settings
from app.services.cezih.exceptions import CezihAuthError
from app.services.cezih.models import OAuth2TokenResponse

logger = logging.getLogger(__name__)

_token_cache: OAuth2TokenResponse | None = None
_token_acquired_at: float = 0.0
_last_failure_at: float = 0.0
_FAILURE_COOLDOWN = 60.0  # seconds to wait before retrying after a failure
_lock = asyncio.Lock()


def _is_token_valid() -> bool:
    if _token_cache is None:
        return False
    buffer = 30  # refresh 30s before expiry
    return (time.monotonic() - _token_acquired_at) < (_token_cache.expires_in - buffer)


async def get_oauth_token(*, client: httpx.AsyncClient) -> str:
    """Get a valid OAuth2 access token, using cache or fetching a new one."""
    if _is_token_valid():
        return _token_cache.access_token  # type: ignore[union-attr]

    # Negative cache: don't retry too quickly after a failure (e.g. DNS unreachable)
    if _last_failure_at and (time.monotonic() - _last_failure_at) < _FAILURE_COOLDOWN:
        raise CezihAuthError("CEZIH OAuth2 recently failed, waiting before retry")

    async with _lock:
        if _is_token_valid():
            return _token_cache.access_token  # type: ignore[union-attr]
        if _last_failure_at and (time.monotonic() - _last_failure_at) < _FAILURE_COOLDOWN:
            raise CezihAuthError("CEZIH OAuth2 recently failed, waiting before retry")
        return await _fetch_new_token(client)


async def _fetch_new_token(client: httpx.AsyncClient) -> str:
    global _token_cache, _token_acquired_at, _last_failure_at

    if not settings.CEZIH_OAUTH2_URL or not settings.CEZIH_CLIENT_ID:
        _last_failure_at = time.monotonic()
        raise CezihAuthError("CEZIH OAuth2 URL and Client ID must be configured when CEZIH_MODE=real")

    token_data = {
        "grant_type": "client_credentials",
        "client_id": settings.CEZIH_CLIENT_ID,
        "client_secret": settings.CEZIH_CLIENT_SECRET,
    }

    try:
        logger.info("CEZIH OAuth2: fetching token from %s", settings.CEZIH_OAUTH2_URL)
        response = await client.post(
            settings.CEZIH_OAUTH2_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=settings.CEZIH_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.ConnectError as e:
        _last_failure_at = time.monotonic()
        raise CezihAuthError(
            f"Cannot connect to OAuth2 server at {settings.CEZIH_OAUTH2_URL}. Is VPN connected?"
        ) from e
    except httpx.TimeoutException as e:
        _last_failure_at = time.monotonic()
        raise CezihAuthError(
            f"OAuth2 token request timed out after {settings.CEZIH_TIMEOUT}s"
        ) from e
    except httpx.HTTPStatusError as e:
        _last_failure_at = time.monotonic()
        raise CezihAuthError(
            f"OAuth2 token request failed: HTTP {e.response.status_code} - {e.response.text[:200]}"
        ) from e

    token_response = OAuth2TokenResponse.model_validate_json(response.text)
    _token_cache = token_response
    _token_acquired_at = time.monotonic()
    _last_failure_at = 0.0  # clear failure state on success

    logger.info("CEZIH OAuth2: token acquired (expires_in=%ds)", token_response.expires_in)
    return token_response.access_token


def invalidate_token() -> None:
    """Force token refresh on next request (e.g. after 401 response)."""
    global _token_cache, _token_acquired_at, _last_failure_at
    _token_cache = None
    _token_acquired_at = 0.0
    _last_failure_at = 0.0  # allow immediate retry after explicit invalidation
