"""Unit tests for NalazPDFGenerator — missing/empty field resilience."""

from datetime import date

import pytest

from app.services.pdf_generator import (
    NalazPDFGenerator,
    _escape,
    _format_date_hr,
    _format_phone,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _full_tenant() -> dict:
    return {
        "naziv": "Poliklinika Sunce",
        "vrsta": "poliklinika",
        "adresa": "Ilica 42",
        "grad": "Zagreb",
        "postanski_broj": "10000",
        "oib": "12345678901",
        "telefon": "01 234 5678",
        "web": "www.sunce.hr",
    }


def _full_doctor() -> dict:
    return {
        "ime": "Marko",
        "prezime": "Marković",
        "titula": "dr. med.",
    }


def _full_patient() -> dict:
    return {
        "ime": "Ana",
        "prezime": "Anić",
        "datum_rodjenja": "1990-05-15",
        "spol": "Z",
        "oib": "98765432101",
        "mbo": "123456789",
        "adresa": "Vukovarska 10",
        "grad": "Split",
        "postanski_broj": "21000",
    }


def _full_record() -> dict:
    return {
        "datum": "2026-04-05",
        "tip": "specijalisticki_nalaz",
        "dijagnoza_mkb": "J06.9",
        "dijagnoza_tekst": "Akutna infekcija gornjih dišnih putova",
        "sadrzaj": "Pacijent se javlja zbog kašlja i povišene temperature.\n"
                   "Faringijski zid hiperemičan. Auskultatorno uredno.",
        "preporucena_terapija": [
            {
                "naziv": "Ibuprofen",
                "jacina": "400mg",
                "oblik": "tableta",
                "doziranje": "3x1",
                "napomena": "Uz obrok",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestGenerateFullData:
    def test_returns_valid_pdf_bytes(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=_full_record(),
        ).generate()

        assert isinstance(pdf, bytes)
        assert len(pdf) > 500
        assert pdf[:5] == b"%PDF-"


class TestGenerateMinimalRecord:
    def test_record_with_only_sadrzaj(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={"sadrzaj": "Minimalan nalaz.", "datum": "2026-04-05"},
        ).generate()

        assert pdf[:5] == b"%PDF-"

    def test_completely_empty_record(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={},
        ).generate()

        assert pdf[:5] == b"%PDF-"


class TestGenerateEmptyDicts:
    def test_empty_patient(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient={},
            record=_full_record(),
        ).generate()

        assert pdf[:5] == b"%PDF-"

    def test_empty_tenant(self):
        pdf = NalazPDFGenerator(
            tenant={},
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=_full_record(),
        ).generate()

        assert pdf[:5] == b"%PDF-"

    def test_empty_doctor(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor={},
            patient=_full_patient(),
            record=_full_record(),
        ).generate()

        assert pdf[:5] == b"%PDF-"

    def test_all_empty_dicts(self):
        pdf = NalazPDFGenerator(
            tenant={},
            doctor={},
            patient={},
            record={},
        ).generate()

        assert pdf[:5] == b"%PDF-"


class TestGenerateNoneDicts:
    """Passing None instead of a dict should not crash (coerced to {})."""

    def test_none_tenant(self):
        pdf = NalazPDFGenerator(
            tenant=None,
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_none_doctor(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=None,
            patient=_full_patient(),
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_none_patient(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=None,
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_none_record(self):
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=None,
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestGenerateOptionalSections:
    def test_no_diagnosis_skips_section(self):
        record = _full_record()
        del record["dijagnoza_mkb"]
        del record["dijagnoza_tekst"]

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_no_therapy_skips_section(self):
        record = _full_record()
        del record["preporucena_terapija"]

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_empty_therapy_list(self):
        record = _full_record()
        record["preporucena_terapija"] = []

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestGenerateNoneFieldValues:
    def test_none_patient_fields(self):
        patient = {
            "ime": None,
            "prezime": None,
            "datum_rodjenja": None,
            "spol": None,
            "oib": None,
            "mbo": None,
            "adresa": None,
            "grad": None,
            "postanski_broj": None,
        }
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=patient,
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_none_tenant_fields(self):
        tenant = {
            "naziv": None,
            "vrsta": None,
            "adresa": None,
            "grad": None,
            "postanski_broj": None,
            "oib": None,
            "telefon": None,
            "web": None,
        }
        pdf = NalazPDFGenerator(
            tenant=tenant,
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_none_record_fields(self):
        record = {
            "datum": None,
            "tip": None,
            "dijagnoza_mkb": None,
            "dijagnoza_tekst": None,
            "sadrzaj": None,
            "preporucena_terapija": None,
        }
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestGenerateSpecialCharacters:
    def test_xml_unsafe_chars_in_patient(self):
        patient = _full_patient()
        patient["ime"] = "Ana <script>"
        patient["prezime"] = "O'Brien & Müller"
        patient["adresa"] = "Ulica <br> 5 & Co."

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=patient,
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_xml_unsafe_chars_in_sadrzaj(self):
        record = _full_record()
        record["sadrzaj"] = "Temp > 38°C, pH < 7.0 & leukociti ↑"

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_xml_unsafe_chars_in_diagnosis(self):
        record = _full_record()
        record["dijagnoza_tekst"] = "Stanje <akutno> & kronično"

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestRecordTypeLabel:
    def test_known_tip_maps_to_label(self):
        gen = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={"tip": "epikriza", "sadrzaj": "Test."},
        )
        assert gen.record_type_label == "Epikriza"

    def test_unknown_tip_uses_raw_value(self):
        gen = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={"tip": "Pregled", "sadrzaj": "Test."},
        )
        assert gen.record_type_label == "Pregled"

    def test_missing_tip_defaults_to_nalaz(self):
        gen = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={"sadrzaj": "Test."},
        )
        assert gen.record_type_label == "Nalaz"

    def test_explicit_label_overrides_tip(self):
        gen = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record={"tip": "epikriza", "sadrzaj": "Test."},
            record_type_label="Custom Label",
        )
        assert gen.record_type_label == "Custom Label"


class TestFormatDateHr:
    def test_none_returns_dash(self):
        assert _format_date_hr(None) == "—"

    def test_date_object(self):
        assert _format_date_hr(date(2026, 4, 5)) == "05.04.2026."

    def test_valid_iso_string(self):
        assert _format_date_hr("2026-04-05") == "05.04.2026."

    def test_malformed_string_short(self):
        assert _format_date_hr("2026") == "2026"

    def test_malformed_string_garbage(self):
        assert _format_date_hr("not-a-date") == "not-a-date"

    def test_empty_string(self):
        assert _format_date_hr("") == ""


class TestEscapeFunction:
    def test_none_returns_empty(self):
        assert _escape(None) == ""

    def test_empty_string(self):
        assert _escape("") == ""

    def test_ampersand(self):
        assert _escape("A & B") == "A &amp; B"

    def test_angle_brackets(self):
        assert _escape("<tag>") == "&lt;tag&gt;"

    def test_integer_crashes(self):
        with pytest.raises(AttributeError):
            _escape(123)

    def test_bool_crashes(self):
        with pytest.raises(AttributeError):
            _escape(True)


class TestDateObjectInRecord:
    def test_record_datum_as_date_object(self):
        record = _full_record()
        record["datum"] = date(2026, 4, 5)

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_patient_datum_rodjenja_as_date_object(self):
        patient = _full_patient()
        patient["datum_rodjenja"] = date(1990, 5, 15)

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=patient,
            record=_full_record(),
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestTherapyEdgeCases:
    def test_therapy_items_with_none_values(self):
        record = _full_record()
        record["preporucena_terapija"] = [
            {"naziv": None, "jacina": None, "oblik": None, "doziranje": None, "napomena": None},
        ]
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_therapy_item_empty_dict(self):
        record = _full_record()
        record["preporucena_terapija"] = [{}]

        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"

    def test_therapy_item_partial_fields(self):
        record = _full_record()
        record["preporucena_terapija"] = [
            {"naziv": "Ibuprofen"},
        ]
        pdf = NalazPDFGenerator(
            tenant=_full_tenant(),
            doctor=_full_doctor(),
            patient=_full_patient(),
            record=record,
        ).generate()
        assert pdf[:5] == b"%PDF-"


class TestFormatPhone:
    # --- International +385 ---
    def test_plus385_mobile(self):
        assert _format_phone("+38591234567") == "+385 91 234 567"

    def test_plus385_mobile_longer(self):
        assert _format_phone("+385912345678") == "+385 91 234 5678"

    def test_00385_mobile(self):
        assert _format_phone("0038591234567") == "+385 91 234 567"

    def test_plus385_zagreb_landline(self):
        assert _format_phone("+38512345678") == "+385 1 234 5678"

    # --- Local 0xx ---
    def test_local_mobile_slash(self):
        assert _format_phone("091/234-567") == "091 234 567"

    def test_local_mobile_dash(self):
        assert _format_phone("092-123-321") == "092 123 321"

    def test_local_mobile_spaces(self):
        assert _format_phone("091 234 567") == "091 234 567"

    def test_local_mobile_no_separator(self):
        assert _format_phone("091234567") == "091 234 567"

    def test_zagreb_landline_slash(self):
        assert _format_phone("01/234-5678") == "01 234 5678"

    def test_zagreb_landline_no_separator(self):
        assert _format_phone("012345678") == "01 234 5678"

    def test_split_landline(self):
        assert _format_phone("021/345-678") == "021 345 678"

    # --- Edge cases ---
    def test_none(self):
        assert _format_phone(None) == ""

    def test_empty(self):
        assert _format_phone("") == ""

    def test_short_number_passthrough(self):
        assert _format_phone("112") == "112"

    def test_already_formatted(self):
        assert _format_phone("+385 91 234 567") == "+385 91 234 567"

    def test_pdf_renders_with_various_phone_formats(self):
        """All phone formats should produce a valid PDF."""
        phones = [
            "+38591234567",
            "0038591234567",
            "091/234-567",
            "092-123-321",
            "01 234 5678",
            "091 234 567",
            None,
            "",
        ]
        for phone in phones:
            tenant = _full_tenant()
            tenant["telefon"] = phone
            pdf = NalazPDFGenerator(
                tenant=tenant,
                doctor=_full_doctor(),
                patient=_full_patient(),
                record=_full_record(),
            ).generate()
            assert pdf[:5] == b"%PDF-", f"Failed for phone: {phone!r}"
