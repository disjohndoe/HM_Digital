"""Tests for backend/app/services/cezih/client.py — FHIR HTTP client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.cezih.client import CezihFhirClient
from app.services.cezih.exceptions import (
    CezihConnectionError,
    CezihFhirError,
    CezihTimeoutError,
)


def _make_mock_client(status_code=200, json_body=None, text=""):
    """Build a mock httpx.AsyncClient and a response."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_body or {}
    response.text = text
    response.headers = {}

    mock_http = AsyncMock()
    mock_http.request = AsyncMock(return_value=response)
    return mock_http, response


@patch("app.services.cezih.client.get_oauth_token", new_callable=AsyncMock, return_value="test-token")
@patch("app.services.cezih.client.settings")
class TestCezihFhirClient:

    @pytest.mark.asyncio
    async def test_get_success(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        body = {"resourceType": "Bundle", "entry": []}
        mock_http, _ = _make_mock_client(200, body)

        client = CezihFhirClient(mock_http)
        result = await client.get("test/path")

        assert result["resourceType"] == "Bundle"
        mock_http.request.assert_called_once()
        call_args = mock_http.request.call_args
        assert call_args[0][0] == "GET"
        assert "test-token" in call_args[1]["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_post_success(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        body = {"resourceType": "DocumentReference", "id": "doc-1"}
        mock_http, _ = _make_mock_client(201, body)

        client = CezihFhirClient(mock_http)
        result = await client.post("test/path", json_body={"key": "val"})

        assert result["id"] == "doc-1"

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        client = CezihFhirClient(mock_http)
        with pytest.raises(CezihConnectionError, match="Cannot connect"):
            await client.get("test")

    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=httpx.TimeoutException("Timed out"))

        client = CezihFhirClient(mock_http)
        with pytest.raises(CezihTimeoutError, match="timed out"):
            await client.get("test")

    @pytest.mark.asyncio
    async def test_fhir_operation_outcome_error(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        body = {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "error", "diagnostics": "Patient not found"}],
        }
        mock_http, _ = _make_mock_client(404, body)

        client = CezihFhirClient(mock_http)
        with pytest.raises(CezihFhirError, match="Patient not found"):
            await client.get("test")

    @pytest.mark.asyncio
    async def test_non_fhir_4xx_error(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        mock_http, _ = _make_mock_client(403, {}, text="Forbidden")

        client = CezihFhirClient(mock_http)
        with pytest.raises(CezihFhirError, match="403"):
            await client.get("test")

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_settings, mock_token):
        mock_settings.CEZIH_FHIR_BASE_URL = "https://certws2.cezih.hr"
        mock_settings.CEZIH_TIMEOUT = 30
        mock_settings.CEZIH_RETRY_ATTEMPTS = 3

        mock_http, _ = _make_mock_client(200, {"resourceType": "Bundle"})

        client = CezihFhirClient(mock_http)
        assert await client.health_check() is True
