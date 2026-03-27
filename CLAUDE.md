# HM Digital — Medical MVP (Polyclinic Patient Management + CEZIH)

## What This Is

Cloud-based patient management system for Croatian private polyclinics and medical practices, with native CEZIH integration. Competes with Toscana (UX) and AdriaSoft (compliance).

**Hard deadline:** 1 May 2026 (Zakon o podacima i informacijama u zdravstvu, NN 14/2019, čl. 28 — mandatory CEZIH for all providers)
**Market:** 2,488 private healthcare institutions in Croatia
**Model:** Cloud SaaS — 14-day free trial → Solo €79/mo (1 user) | Poliklinika €199/mo (2-5 users) | Poliklinika+ po dogovoru (5-15+) + optional onboarding
**Lead list:** docs/medical_leads.csv (4,986 clinics, 2,884 with phone numbers)

## Project Structure

```
MEDICAL_MVP/
├── backend/          # FastAPI — REST API + WebSocket + CEZIH mock
├── frontend/         # Next.js — Patient management UI
├── local-agent/      # Tauri 2.x desktop app — smart card + VPN + WebSocket bridge
└── docs/
    ├── roadmap.md             # Master status tracker + timeline + all contacts
    ├── competitors.md         # Deep-dive competitive analysis (19 vendors verified)
    ├── cezih-technical.md     # VPN, PKI, SOAP, HL7 CDA, G9 specs
    ├── go-to-market.md        # Sales strategy, professional association partnerships, conferences, outreach
    └── implementation-plan.md # Full build spec — DB schema, API, UI, phases (junior-friendly)
```

## Tech Stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, SQLAlchemy async, PostgreSQL
- **Local Agent:** Tauri 2.x (Rust), tokio-tungstenite, system tray — optional, reads AKD smart card, manages VPN
- **CEZIH Integration (novi format za privatnike):** FHIR + IHE profili (MHD, PDQm, SVCM, mCSD, PMIR, QEDm), cloud cert ILI smart kartica

## CEZIH Integration Architecture

```
Browser ←→ Cloud Backend (FastAPI) ←→ Local Agent (desktop) ←→ CEZIH
                REST API                  Smart card + VPN         SOAP/XML
```

## Key CEZIH Modules (G9 — SKZZ)

| Module | Description | Format |
|--------|-------------|--------|
| e-Nalaz | Medical findings | HL7 CDA XML |
| e-Uputnica | Referrals (send/receive) | SOAP |
| e-Recept | Prescriptions | SOAP |
| eNaručivanje | Scheduling / waiting lists | SOAP |
| Insurance check | Patient status via MBO | SOAP |

## Croatian Localization

- All UI in Croatian (Hrvatski)
- UTF-8 for šđčćž
- Timezone: Europe/Zagreb
- Currency: EUR
- GDPR compliant

## Development Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | DONE | Environment & scaffolding |
| Phase 1 | DONE | Auth & multi-tenancy |
| Phase 2 | DONE | Patient management |
| Phase 3 | DONE | Appointment scheduling |
| Phase 4 | DONE | Medical records & procedures |
| Phase 5 | DONE | Dashboard & settings |
| Phase 6A | DONE | Plan enforcement (tier limits, session kick, usage API) |
| Phase 6B | DONE | CEZIH mock backend (insurance, e-Nalaz, e-Uputnica, e-Recept) |
| Phase 6C | DONE | CEZIH mock frontend (CEZIH page, insurance check, e-Nalaz send from records) |
| Phase 7 | DONE | Local agent skeleton (Tauri, WebSocket, agent auth, live status, system tray) |
| Phase 8 | DONE | Polish, testing, demo environment (bug fix, middleware, seed data, tests, Docker, mobile) |

## Certification Status

- HZZO certification request: SENT (2026-03-24, routed to helpdesk)
- Test certificate request: SENT (2026-03-24)
- G9 certification: PENDING (waiting for HZZO response)
- Follow up by phone if no response by 2026-03-28

## Competitive Position

Nobody combines modern cloud UX + CEZIH G9 + specialty-agnostic design.

- 12 CEZIH-certified vendors (all legacy desktop UI)
- 5 modern cloud vendors (zero CEZIH)
- Closest competitor: Aplikacija d.o.o. (cloud + CEZIH but older UX)
- See docs/competitors.md for full analysis

## Go-To-Market

Primary channel: HKDM, HLN, and professional associations — many haven't informed members about CEZIH yet. We position as CEZIH education experts.

Key events: Medical conferences (ongoing, leading up to May deadline).

See docs/go-to-market.md for full strategy.
