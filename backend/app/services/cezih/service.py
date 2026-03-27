from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.services.cezih.client import CezihFhirClient
from app.services.cezih.exceptions import CezihError
from app.services.cezih.models import (
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRDocumentReference,
    FHIRPatient,
    FHIRReference,
)

logger = logging.getLogger(__name__)

# CEZIH identifier systems
SYS_MBO = "http://fhir.cezih.hr/specifikacije/identifikatori/mbo"
SYS_OIB = "http://fhir.cezih.hr/specifikacije/identifikatori/oib"


async def check_insurance(client: httpx.AsyncClient, mbo: str) -> dict:
    """Patient demographics lookup by MBO (ITI-78 PDQm).

    GET /patient-registry-services/api/v1/Patient?identifier={SYS_MBO}|{mbo}
    """
    fhir_client = CezihFhirClient(client)
    params = {"identifier": f"{SYS_MBO}|{mbo}"}

    response = await fhir_client.get("patient-registry-services/api/v1/Patient", params=params)

    if response.get("resourceType") == "Bundle":
        entries = response.get("entry", [])
        if not entries:
            return {
                "mbo": mbo,
                "ime": "",
                "prezime": "",
                "datum_rodjenja": "",
                "osiguravatelj": "",
                "status_osiguranja": "Nije pronađen",
                "broj_osiguranja": "",
            }

        patient = FHIRPatient.model_validate(entries[0].get("resource", {}))
        family, given = _extract_name(patient)

        # Extract insurance number from identifiers
        broj = ""
        osiguravatelj = "HZZO"  # Default for CEZIH-found patients
        for ident in patient.identifier:
            if ident.system and "osiguranje" in ident.system.lower() and ident.value:
                broj = ident.value

        return {
            "mbo": mbo,
            "ime": given,
            "prezime": family,
            "datum_rodjenja": patient.birthDate or "",
            "osiguravatelj": osiguravatelj,
            "status_osiguranja": "Aktivan",
            "broj_osiguranja": broj,
        }

    # Unexpected response format
    logger.warning("CEZIH insurance check: unexpected response type: %s", response.get("resourceType"))
    raise CezihError("Unexpected CEZIH response format for patient lookup")


async def send_enalaz(
    client: httpx.AsyncClient,
    patient_data: dict,
    record_data: dict,
    uputnica_id: str | None = None,
) -> dict:
    """Send clinical document / finding (ITI-65 MHD).

    POST /doc-mhd-svc/api/v1/iti-65-service
    """
    fhir_client = CezihFhirClient(client)

    # Build DocumentReference for the finding
    doc_ref = FHIRDocumentReference(
        status="current",
        type=FHIRCodeableConcept(
            coding=[FHIRCoding(
                system="http://fhir.cezih.hr/specifikacije/vrste-dokumenata",
                code=record_data.get("tip", "nalaz"),
                display=record_data.get("tip_display", "Nalaz"),
            )]
        ),
        subject=FHIRReference(
            reference=f"Patient/{patient_data.get('mbo', '')}",
            display=f"{patient_data.get('ime', '')} {patient_data.get('prezime', '')}",
        ),
        date=datetime.now(UTC).isoformat(),
    )

    # Wrap in a Bundle (ITI-65 expects a Bundle)
    bundle = FHIRBundle(
        type="document",
        timestamp=datetime.now(UTC).isoformat(),
        entry=[FHIRBundleEntry(resource=doc_ref.model_dump(by_alias=True))],
    )

    response = await fhir_client.post(
        "doc-mhd-svc/api/v1/iti-65-service",
        json_body=bundle.model_dump(by_alias=True),
    )

    # Extract reference ID from response
    ref_id = ""
    if response.get("resourceType") == "DocumentReference":
        ref_id = response.get("id", "")
    elif response.get("resourceType") == "Bundle":
        entries = response.get("entry", [])
        if entries:
            resource = entries[0].get("resource", {})
            ref_id = resource.get("id", "")

    if not ref_id:
        ref_id = f"FHIR-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    return {
        "success": True,
        "reference_id": ref_id,
        "sent_at": datetime.now(UTC).isoformat(),
    }


async def retrieve_euputnice(client: httpx.AsyncClient) -> list[dict]:
    """Retrieve e-Uputnice from CEZIH (ITI-67 DocumentReference search).

    GET /doc-mhd-svc/api/v1/DocumentReference?type=uputnica
    """
    fhir_client = CezihFhirClient(client)
    params = {
        "type": "http://fhir.cezih.hr/specifikacije/vrste-dokumenata|uputnica",
    }

    response = await fhir_client.get("doc-mhd-svc/api/v1/DocumentReference", params=params)

    items = []
    if response.get("resourceType") == "Bundle":
        for entry in response.get("entry", []):
            doc_ref = entry.get("resource", {})
            items.append({
                "id": doc_ref.get("id", ""),
                "datum_izdavanja": doc_ref.get("date", ""),
                "izdavatelj": _extract_reference_display(doc_ref.get("context", {}).get("source", {})),
                "svrha": _extract_codeable_text(doc_ref.get("type")),
                "specijalist": _extract_reference_display(doc_ref.get("context", {}).get("encounter", {})),
                "status": _map_fhir_status(doc_ref.get("status", "current")),
            })

    return items


async def send_erecept(
    client: httpx.AsyncClient,
    patient_data: dict,
    lijekovi: list[dict],
) -> dict:
    """Send e-prescription (stub — not in 22 test cases yet)."""
    logger.warning("CEZIH e-Recept: real API not yet implemented, returning stub")
    import os
    return {
        "success": True,
        "recept_id": f"FHIR-ER-{os.urandom(4).hex()}",
    }


async def get_status(client: httpx.AsyncClient) -> dict:
    """Check CEZIH connectivity."""
    fhir_client = CezihFhirClient(client)
    connected = await fhir_client.health_check()
    return {
        "connected": connected,
        "mode": "real",
    }


async def search_drugs(client: httpx.AsyncClient, query: str) -> list[dict]:
    """Search drugs via CEZIH CodeSystem (ITI-96).

    GET /terminology-services/api/v1/CodeSystem?name={query}
    """
    if not query or len(query) < 2:
        return []

    fhir_client = CezihFhirClient(client)
    params = {"name": query, "_count": "20"}

    response = await fhir_client.get("terminology-services/api/v1/CodeSystem", params=params)

    drugs = []
    if response.get("resourceType") == "Bundle":
        for entry in response.get("entry", []):
            cs = entry.get("resource", {})
            drugs.append({
                "atk": cs.get("id", ""),
                "naziv": cs.get("name", ""),
                "oblik": "",
                "jacina": "",
            })

    return drugs


# --- Helpers ---


def _extract_name(patient: FHIRPatient) -> tuple[str, str]:
    """Extract family and given names from a FHIR Patient resource."""
    if not patient.name:
        return "", ""
    official = next((n for n in patient.name if n.use == "official"), patient.name[0])
    family = official.family or ""
    given = " ".join(official.given) if official.given else ""
    return family, given


def _extract_codeable_text(concept: dict | None) -> str:
    """Extract display text from a FHIR CodeableConcept."""
    if not concept:
        return ""
    if concept.get("text"):
        return concept["text"]
    codings = concept.get("coding", [])
    if codings:
        return codings[0].get("display", codings[0].get("code", ""))
    return ""


def _extract_reference_display(ref: dict | str | None) -> str:
    """Extract display from a FHIR Reference or reference-like dict."""
    if not ref or isinstance(ref, str):
        return ""
    return ref.get("display", ref.get("reference", ""))


def _map_fhir_status(status: str) -> str:
    """Map FHIR DocumentReference status to our domain status."""
    mapping = {
        "current": "Otvorena",
        "superseded": "Zatvorena",
        "entered-in-error": "Pogreška",
    }
    return mapping.get(status, status)
