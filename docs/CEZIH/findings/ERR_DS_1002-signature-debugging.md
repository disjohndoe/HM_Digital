---
date: 2026-04-09
topic: ERR_DS_1002 root cause
status: resolved
---

# ERR_DS_1002 — Root Cause: NOT the Signature

## KEY CONCLUSION

**ERR_DS_1002 is NOT a signature problem. Stop debugging signature format.**

Proven by sending a Bundle with NO `signature` field → same ERR_DS_1002 (commit ec92dcc).
54 commits of signature experiments were wasted effort. The real issue is elsewhere.

## Primary Suspects (investigate in this order)

### 1. Missing `Encounter.type` slices (FIXED 2026-04-09)
The `hr-encounter` profile (cezih.osnova 0.2.3) defines two type slices:
- `VrstaPosjete` → `CodeSystem/vrsta-posjete` (prisutnost pacijenta)
- `TipPosjete` → `CodeSystem/hr-tip-posjete` (primarna/SKZZ/hosp.)

**Our Encounter was missing BOTH.** Parameters existed in the function signature but were never used. Fixed in `message_builder.py` — both slices now included.

**This is the most likely cause of ERR_DS_1002.** Retest with the fix before investigating anything else.

### 2. Certificate not linked to practitioner
mTLS cert (OIB 15881939647) may not be registered as authorized for test doctor HZJZ 7659059 / institution 999001464.

### 3. Other FHIR validation failures
ERR_DS_1002 may be a generic server-side validation error, not specifically about digital signatures. The error code name is misleading.

### 4. Test environment misconfiguration
Test env provisioned 2026-04-07, may not be fully set up.

## UPDATE 2026-04-09 15:48 — JWS fix changes error type!

Switched from raw signing to proper JWS (RFC 7515 with x5c cert chain).

**Before (raw signing):** `OperationOutcome.issue.code = "invalid"` — format rejected
**After (JWS with x5c):** `OperationOutcome.issue.code = "business-rule"` — format ACCEPTED, business rule rejects

This proves: the signature FORMAT is now correct. The remaining ERR_DS_1002 is a
BUSINESS RULE rejection — most likely the signing certificate is not registered
with CEZIH for our test practitioner/institution.

## UPDATE 2026-04-09 16:38 — Extsigner API fully reverse-engineered!

### Confirmed API Schema (certws2.cezih.hr:8443)

```
POST /services-router/gateway/extsigner/api/sign
Content-Type: application/json
Auth: mTLS session (smart card via SChannel)

{
    "oib": "15881939647",
    "sourceSystem": "HM_DIGITAL",
    "requestId": "<uuid>",
    "documents": [{
        "documentType": "FHIR_MESSAGE",   // enum: FHIR_MESSAGE, FHIR_DOCUMENT
        "mimeType": "JSON",               // enum: JSON, XML (NOT MIME strings!)
        "base64Document": "<base64-encoded-FHIR-bundle>",
        "messageId": "<uuid>"
    }]
}
```

### Field Discovery Method
- Empty `{}` body → revealed top-level: `oib`, `sourceSystem`, `requestId`, `documents`
- Empty `[{}]` doc → revealed doc fields: `documentType`, `mimeType`, `base64Document`, `messageId`
- Enum brute-force → documentType: `FHIR_MESSAGE` (message bundles), `FHIR_DOCUMENT` (doc bundles)
- Enum brute-force → mimeType: `JSON`, `XML` (other values treated as null)
- Service name: `rdss-service` (Remote Digital Signing Service)

### Current Blocker: Mobile Signing Activation
Request reaches AKD/Certilia backend → **ERROR_CODE_0025** code 31:
"Korisnik trenutno ne moze potpisati na mobitelu." (User cannot sign on mobile)

This means:
1. API format is 100% CORRECT
2. The signing backend requires Certilia mobile app confirmation (2FA)
3. Need to activate/configure AKD Potpis mobile app for OIB 15881939647
4. Or ask HZZO if test environment has a bypass for mobile confirmation

### Interesting: FHIR_DOCUMENT combo
- `FHIR_DOCUMENT` + `JSON` → `INVALID_JSON_PAYLOAD` (code A250) — likely expects different Bundle structure
- `FHIR_MESSAGE` + `XML` → `UNSUPPORTED_COMBINATION_SIGNATURE_FORMAT_SUBFORMAT` (code 732)

### UPDATE 2026-04-09 17:09 — Extsigner confirmed on BOTH paths!

Expanded test_extsigner.py with T9-T12. Results:

| Test | Endpoint | Auth | HTTP | Result |
|------|----------|------|------|--------|
| T9 | certpubws (public) | OAuth2 Bearer | 401 | ERROR_CODE_0025 code 31 — "ne može potpisati na mobitelu" |
| T10 | certws2:8443 (VPN) | mTLS smart card | 500 | ERROR_CODE_0025 code 31 — same message |
| T11 | certws2:8443 (VPN) | mTLS + Bearer | 500 | HTML 401 (auth conflict) |
| T12 | certpubws (public) | mTLS only | 401 | empty body (needs Bearer) |

**KEY FINDINGS:**
1. **Both paths (T9 + T10) reach the AKD signing backend** — API format is 100% correct
2. **Same blocker on both:** AKD Potpis mobile app not activated for OIB 15881939647
3. HTTP status codes are misleading (401/500) — the error body confirms the request WAS processed
4. certpubws requires Bearer token (T12 mTLS-only = empty 401)
5. Don't mix mTLS + Bearer (T11 = auth conflict)

**Also fixed:** `build_encounter_create()` was missing Encounter.type slices (vrstaPosjete/tipPosjete) — params existed but were never used. Fixed to match `build_encounter_update()`.

### Next Steps

1. **Install/configure AKD Potpis mobile app** for OIB 15881939647 — this is the ONLY remaining blocker for cloud signing
2. **Or contact HZZO/AKD** — ask if test env mobile signing needs special activation
3. **Once mobile signing works:** extsigner returns signed Bundle → plug into $process-message → no agent needed for signing
4. **Agent is still needed** for VPN access (clinical endpoints on port 8443)

## RESOLVED (2026-04-10)

**Root cause:** Missing Encounter.type slices (VrstaPosjete + TipPosjete) — fixed in `message_builder.py`.
**Working method:** Extsigner (Certilia remote signing) — smart card NCrypt JWS still fails with business-rule rejection (cert not registered), but extsigner bypasses this entirely.
**TC12 verified live 2026-04-10** — create visit works end-to-end via extsigner + `$process-message`.

Note: The ITI-65 document submission 403 is a SEPARATE issue (wrong bundle type — message vs transaction). See `ITI-65-403-blocker.md`.

## Evidence: Signature Is NOT the Cause

```
POST encounter-services/api/v1/$process-message → 400 (232ms)
Body: 2389 chars, NO "signature" field in Bundle
Response: ERR_DS_1002 (same error as with signature)
```

54 commits tested every signature permutation — JWS, raw concat, detached, with/without x5c/jwk, JCS sorted, unsorted, double base64, single base64, CMS/PKCS#7. ALL returned ERR_DS_1002.

## Signature Format (for later, after message structure is confirmed)

Per spec 3.4 and Simplifier StructureDefinition `hr-request-message`:
- Standard JWS compact (RFC 7515) with double base64
- JOSE header: `alg` (RS1 for smart card), `jwk`, `x5c`
- `sigFormat`/`targetFormat`/`onBehalfOf` PROHIBITED (max 0)
- See `cezih-official-signature-format.md` for full details
