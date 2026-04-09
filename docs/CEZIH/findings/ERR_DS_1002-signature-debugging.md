---
date: 2026-04-09
topic: signing
status: active
---

# ERR_DS_1002 — Signature Debugging History

## CRITICAL FINDING (2026-04-09 session 2)

**ERR_DS_1002 occurs even WITHOUT any signature in the Bundle.**

Sending a Bundle with NO `signature` field at all returns the exact same ERR_DS_1002 error. This proves:
- ERR_DS_1002 is **NOT about our JWS signature format**
- The error is about something else entirely (possibly mTLS cert linkage, session-level signing, or a validation unrelated to Bundle.signature)
- All format permutations (JWS, detached JWS, raw concat) were irrelevant

### Evidence
```
POST encounter-services/api/v1/$process-message → 400 (232ms)
Body: 2389 chars, NO "signature" field in Bundle
Response: ERR_DS_1002 (same error as with signature)
```

## Chronological Attempts

### Session 1 (2026-04-08)

| # | Format | JOSE Header | Result |
|---|--------|-------------|--------|
| 1 | JWS compact | kid+alg | HAPI-1821 (dots invalid) |
| 2 | Raw concatenation | kid+alg | ERR_DS_1002 |
| 3 | Raw bundle hash | none | ERR_DS_1002 |
| 4 | JWS+JCS+double-b64 | kid+alg | ERR_DS_1002 |
| 5 | JWS+JCS+double-b64 | kid+alg+x5c | ERR_DS_1002 |
| 6 | JWS+JCS+double-b64 | kid+alg (minimal) | ERR_DS_1002 |
| 7 | JWS+JCS+double-b64 | kid+alg+jwk+x5c | ERR_DS_1002 |

POST redirect bug found and fixed (CURLOPT_POSTREDIR).

### Session 2 (2026-04-09)

| # | Format | JOSE Header | Data Field | Sorting | Result |
|---|--------|-------------|------------|---------|--------|
| 8 | JWS+JCS+double-b64 | alg+kid+jwk+x5c (full) | data="" | JCS | ERR_DS_1002 |
| 9 | Detached JWS (empty payload) | alg+kid+jwk+x5c (full) | data="" | JCS | ERR_DS_1002 |
| 10 | Raw concat+single-b64 | alg+kid (minimal) | data="" | Not sorted | ERR_DS_1002 |
| **11** | **NO SIGNATURE AT ALL** | **N/A** | **N/A** | **N/A** | **ERR_DS_1002** |

Self-verification (BCryptVerifySignature) PASSED in attempts 8-10.

## Root Cause Analysis

ERR_DS_1002 is NOT triggered by the Bundle signature. Possible causes:
1. **Certificate not linked to practitioner** — mTLS cert (OIB 15881939647) may not be registered as authorized for test doctor HZJZ 7659059 / institution 999001464
2. **Session-level signing** — CEZIH may expect a different kind of digital signature at the HTTP/session level, not in the FHIR Bundle
3. **Generic validation error** — ERR_DS_1002 may be a catch-all error code that includes non-signature validation failures
4. **Test environment misconfiguration** — The test environment was provisioned 2026-04-07 but may not be fully set up

## Action Items
- [ ] **Contact HZZO** — Ask specifically what ERR_DS_1002 means for an UNSIGNED Bundle
- [ ] Ask if the test cert needs explicit registration for the test doctor
- [ ] Ask for server-side logs showing what validation fails
- [ ] Ask whether Bundle.signature is required at all for $process-message
