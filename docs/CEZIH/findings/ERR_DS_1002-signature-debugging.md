---
date: 2026-04-09
topic: ERR_DS_1002 root cause
status: active
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

## Next Steps

1. **Deploy the Encounter.type fix and retest TC12** — if this resolves ERR_DS_1002, the 54 signature commits were all chasing the wrong problem
2. If still failing, contact HZZO and ask what ERR_DS_1002 means for a valid Bundle
3. Only after confirming the message structure is correct, switch signing to JWS format per spec 3.4

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
