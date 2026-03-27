"""Tests for backend/app/services/cezih/dispatcher.py — mock/real routing."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.cezih.exceptions import CezihError


class TestDispatcherMockMode:

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_insurance_check_mock(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["insurance_check"])
        result = await disp.insurance_check("123456789")
        assert result["mock"] is True
        assert result["mbo"] == "123456789"
        assert "ime" in result

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_cezih_status_mock(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["cezih_status"])
        result = await disp.cezih_status()
        assert result["mock"] is True
        assert result["mode"] == "mock"

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_drug_search_valid_query(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["drug_search"])
        result = disp.drug_search("para")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "naziv" in result[0]

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_drug_search_empty_query(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["drug_search"])
        result = disp.drug_search("")
        assert result == []

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_drug_search_short_query(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["drug_search"])
        result = disp.drug_search("P")
        assert result == []

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_sign_document_mock(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["sign_document"])
        result = await disp.sign_document(b"test document")
        assert result["mock"] is True
        assert result["success"] is True
        assert "signature" in result

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_signing_health_check_mock(self, mock_settings):
        mock_settings.CEZIH_MODE = "mock"
        disp = __import__("app.services.cezih.dispatcher", fromlist=["signing_health_check"])
        result = await disp.signing_health_check()
        assert result["mock"] is True
        assert result["reachable"] is True


class TestDispatcherRealMode:

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_insurance_check_real_success(self, mock_settings):
        mock_settings.CEZIH_MODE = "real"
        mock_http = AsyncMock()

        mock_real = AsyncMock(return_value={
            "mbo": "999990260", "ime": "Goran", "prezime": "Pac",
            "datum_rodjenja": "1990-01-01", "osiguravatelj": "HZZO",
            "status_osiguranja": "Aktivan", "broj_osiguranja": "HR-123",
        })

        with patch("app.services.cezih.dispatcher.real_service.check_insurance", mock_real):
            disp = __import__("app.services.cezih.dispatcher", fromlist=["insurance_check"])
            result = await disp.insurance_check("999990260", http_client=mock_http)

        assert result["mock"] is False
        assert result["ime"] == "Goran"
        mock_real.assert_called_once_with(mock_http, "999990260")

    @pytest.mark.asyncio
    @patch("app.services.cezih.dispatcher.settings")
    async def test_insurance_check_real_failure(self, mock_settings):
        mock_settings.CEZIH_MODE = "real"
        mock_http = AsyncMock()

        mock_real = AsyncMock(side_effect=CezihError("VPN not connected"))

        with patch("app.services.cezih.dispatcher.real_service.check_insurance", mock_real):
            disp = __import__("app.services.cezih.dispatcher", fromlist=["insurance_check"])
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await disp.insurance_check("123", http_client=mock_http)
            assert exc_info.value.status_code == 502
