"""Tests for backend/app/services/cezih/service.py — real CEZIH service functions."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.cezih.models import FHIRHumanName, FHIRPatient
from app.services.cezih.service import (
    _extract_codeable_text,
    _extract_name,
    _extract_reference_display,
    _map_fhir_status,
)

# --- Pure helper tests (no mocking needed) ---


class TestExtractName:
    def test_official_priority(self):
        p = FHIRPatient(name=[
            FHIRHumanName(family="Marić", given=["Marko"], use="usual"),
            FHIRHumanName(family="Horvat", given=["Ivan"], use="official"),
        ])
        family, given = _extract_name(p)
        assert family == "Horvat"
        assert given == "Ivan"

    def test_first_name_fallback(self):
        p = FHIRPatient(name=[
            FHIRHumanName(family="Test", given=["A", "B"]),
        ])
        family, given = _extract_name(p)
        assert family == "Test"
        assert given == "A B"

    def test_empty_list(self):
        p = FHIRPatient(name=[])
        family, given = _extract_name(p)
        assert family == ""
        assert given == ""


class TestExtractCodeableText:
    def test_text_priority(self):
        assert _extract_codeable_text({"text": "My text", "coding": [{"display": "Other"}]}) == "My text"

    def test_coding_display(self):
        assert _extract_codeable_text({"coding": [{"display": "Code display"}]}) == "Code display"

    def test_coding_code_fallback(self):
        assert _extract_codeable_text({"coding": [{"code": "ABC"}]}) == "ABC"

    def test_none(self):
        assert _extract_codeable_text(None) == ""

    def test_empty_dict(self):
        assert _extract_codeable_text({}) == ""


class TestExtractReferenceDisplay:
    def test_display(self):
        assert _extract_reference_display({"display": "Dr. Test"}) == "Dr. Test"

    def test_reference_fallback(self):
        assert _extract_reference_display({"reference": "Patient/1"}) == "Patient/1"

    def test_none(self):
        assert _extract_reference_display(None) == ""

    def test_string(self):
        assert _extract_reference_display("Patient/1") == ""


class TestMapFhirStatus:
    def test_current(self):
        assert _map_fhir_status("current") == "Otvorena"

    def test_superseded(self):
        assert _map_fhir_status("superseded") == "Zatvorena"

    def test_entered_in_error(self):
        assert _map_fhir_status("entered-in-error") == "Pogreška"

    def test_unknown(self):
        assert _map_fhir_status("unknown") == "unknown"


# --- Service function tests (need mocking) ---


class TestCheckInsurance:
    @pytest.mark.asyncio
    async def test_patient_found(self):
        """ITI-78 returns a Bundle with a matching Patient resource."""

        mock_client = AsyncMock()
        mock_fhir = AsyncMock()
        mock_fhir.get = AsyncMock(return_value={
            "resourceType": "Bundle",
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "id": "1",
                    "name": [{"family": "Horvat", "given": ["Ivan"], "use": "official"}],
                    "birthDate": "1985-03-15",
                    "identifier": [
                        {
                            "system": "http://fhir.cezih.hr/specifikacije/identifikatori/osiguranje",
                            "value": "HR-123456",
                        },
                    ],
                },
            }],
        })

        with patch("app.services.cezih.service.CezihFhirClient", return_value=mock_fhir):
            svc = __import__(
                "app.services.cezih.service",
                fromlist=["check_insurance"],
            )
            result = await svc.check_insurance(mock_client, "999990260")

        assert result["mbo"] == "999990260"
        assert result["ime"] == "Ivan"
        assert result["prezime"] == "Horvat"
        assert result["status_osiguranja"] == "Aktivan"

    @pytest.mark.asyncio
    async def test_patient_not_found(self):

        mock_client = AsyncMock()
        mock_fhir = AsyncMock()
        mock_fhir.get = AsyncMock(return_value={"resourceType": "Bundle", "entry": []})

        with patch("app.services.cezih.service.CezihFhirClient", return_value=mock_fhir):
            svc = __import__(
                "app.services.cezih.service",
                fromlist=["check_insurance"],
            )
            result = await svc.check_insurance(mock_client, "000000000")

        assert result["status_osiguranja"] == "Nije pronađen"
        assert result["ime"] == ""


class TestSendEnalaz:
    @pytest.mark.asyncio
    async def test_success(self):

        mock_client = AsyncMock()
        mock_fhir = AsyncMock()
        mock_fhir.post = AsyncMock(return_value={
            "resourceType": "DocumentReference",
            "id": "doc-123",
        })

        with patch("app.services.cezih.service.CezihFhirClient", return_value=mock_fhir):
            result = await __import__("app.services.cezih.service", fromlist=["send_enalaz"]).send_enalaz(
                mock_client,
                {"mbo": "999990260", "ime": "Ivan", "prezime": "Horvat"},
                {"tip": "nalaz", "tip_display": "Nalaz"},
            )

        assert result["success"] is True
        assert result["reference_id"] == "doc-123"


class TestSendErecept:
    @pytest.mark.asyncio
    async def test_stub(self):
        """e-Recept is a stub — always returns success."""
        mock_client = AsyncMock()
        service = __import__("app.services.cezih.service", fromlist=["send_erecept"])
        result = await service.send_erecept(mock_client, {"mbo": "123"}, [{"naziv": "Paracetamol"}])
        assert result["success"] is True
        assert "recept_id" in result
