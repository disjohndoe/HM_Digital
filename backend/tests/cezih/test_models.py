"""Tests for backend/app/services/cezih/models.py — Pydantic FHIR models."""

from app.services.cezih.models import (
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIREncounter,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRPatient,
    OAuth2TokenResponse,
    OperationOutcome,
    OperationOutcomeIssue,
)


class TestFHIRIdentifier:
    def test_defaults(self):
        ident = FHIRIdentifier()
        assert ident.system is None
        assert ident.value is None

    def test_with_values(self):
        ident = FHIRIdentifier(system="http://example.com", value="12345")
        assert ident.system == "http://example.com"
        assert ident.value == "12345"


class TestFHIRPatient:
    def test_resource_type(self):
        p = FHIRPatient()
        assert p.resourceType == "Patient"

    def test_full_construction(self):
        p = FHIRPatient(
            id="pat-1",
            identifier=[FHIRIdentifier(system="urn:mbo", value="123")],
            name=[FHIRHumanName(family="Horvat", given=["Ivan"], use="official")],
            birthDate="1985-03-15",
            gender="male",
            active=True,
        )
        assert p.id == "pat-1"
        assert len(p.identifier) == 1
        assert p.name[0].family == "Horvat"
        assert p.name[0].given == ["Ivan"]
        assert p.birthDate == "1985-03-15"
        assert p.active is True

    def test_dump_by_alias(self):
        p = FHIRPatient(id="p1")
        d = p.model_dump()
        assert d["resourceType"] == "Patient"


class TestFHIREncounter:
    def test_alias_handling(self):
        enc = FHIREncounter(status="finished")
        d = enc.model_dump(by_alias=True)
        assert d["class"] is None
        assert d["resourceType"] == "Encounter"


class TestFHIRBundle:
    def test_empty_defaults(self):
        b = FHIRBundle()
        assert b.type is None
        assert b.entry == []
        assert b.total is None

    def test_transaction_bundle(self):
        b = FHIRBundle(
            type="transaction",
            entry=[FHIRBundleEntry(fullUrl="urn:1", resource={"resourceType": "Patient"})],
        )
        assert b.type == "transaction"
        assert len(b.entry) == 1


class TestOperationOutcome:
    def test_first_error_message_with_diagnostics(self):
        oo = OperationOutcome(issue=[
            OperationOutcomeIssue(severity="error", diagnostics="Invalid parameter")
        ])
        assert "Invalid parameter" in oo.first_error_message

    def test_first_error_message_falls_back_to_details_text(self):
        oo = OperationOutcome(issue=[
            OperationOutcomeIssue(
                severity="error",
                details=FHIRCodeableConcept(text="Something went wrong"),
            )
        ])
        assert "Something went wrong" in oo.first_error_message

    def test_no_errors(self):
        oo = OperationOutcome(issue=[])
        assert oo.first_error_message == "Unknown FHIR error"

    def test_skips_warning_severity(self):
        oo = OperationOutcome(issue=[
            OperationOutcomeIssue(severity="warning", diagnostics="Minor issue"),
            OperationOutcomeIssue(severity="error", diagnostics="Real error"),
        ])
        assert "Real error" in oo.first_error_message


class TestOAuth2TokenResponse:
    def test_defaults(self):
        tr = OAuth2TokenResponse(access_token="tok123")
        assert tr.token_type == "Bearer"
        assert tr.expires_in == 300
        assert tr.refresh_expires_in == 1800
        assert tr.scope is None

    def test_custom_values(self):
        tr = OAuth2TokenResponse(
            access_token="tok456",
            expires_in=600,
            scope="read write",
        )
        assert tr.access_token == "tok456"
        assert tr.expires_in == 600
        assert tr.scope == "read write"
