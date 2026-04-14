# State

**Last Updated:** 2026-04-14T00:00:00Z
**Current Work:** M1 MVP Core — Project Bootstrap

---

## Recent Decisions (Last 60 days)

### AD-001: NestJS Modular Monolith over Microservices (2026-04-14)

**Decision:** Single NestJS app with module-per-domain, no microservices
**Reason:** Solo/small team, MVP stage — microservices would add DevOps overhead without benefit
**Trade-off:** Harder to scale individual modules independently later
**Impact:** All modules in `src/modules/`, cross-module communication via EventEmitter2

### AD-002: Supabase as DB + Storage (2026-04-14)

**Decision:** Use Supabase (hosted PostgreSQL) with `@supabase/supabase-js` client
**Reason:** Managed infra, built-in Storage for documents, no self-hosted Postgres needed
**Trade-off:** Vendor lock-in; no ORM (raw Supabase queries for now)
**Impact:** SupabaseService in DatabaseModule, exposed globally

### AD-003: BullMQ for all async work (2026-04-14)

**Decision:** All async operations (iCal sync, alert dispatch) go through BullMQ queues
**Reason:** Reliable retry, scheduling, visibility into job state
**Trade-off:** Requires Redis dependency
**Impact:** Two queues: `ical-sync`, `owner-alerts`

### AD-004: iCal-first for OTA integration (2026-04-14)

**Decision:** v1 uses iCal (read-only sync) instead of official Airbnb/Booking APIs
**Reason:** iCal requires no partnership, works immediately, covers 90% of the MVP need
**Trade-off:** Read-only (can't push availability/pricing); no real-time updates
**Impact:** 15-min sync interval; Airbnb API partnership to be pursued in parallel for M2

### AD-005: TEMP_TENANT_ID placeholder for auth (2026-04-14)

**Decision:** Use hardcoded TEMP_TENANT_ID in controllers for v1
**Reason:** Auth is M2 scope — don't block MVP on it
**Trade-off:** Not multi-tenant safe until M2
**Impact:** All controllers have `const TEMP_TENANT_ID = 'temp-tenant-id'` — replace in M2

### AD-006: Evolution API for WhatsApp (2026-04-14)

**Decision:** Use Evolution API (self-hosted) as WhatsApp gateway
**Reason:** Cost-effective, no per-message pricing for high volume, full control
**Trade-off:** Requires self-hosted instance; API stability dependent on open-source project
**Impact:** MessagingService wraps Evolution API HTTP calls with retry

---

## Active Blockers

_(none)_

---

## Lessons Learned

_(none yet)_

---

## Quick Tasks Completed

_(none yet)_

---

## Deferred Ideas

- [ ] Competitor price monitoring — Captured during: product study
- [ ] Upsell automation (early check-in, late checkout) — Captured during: product study
- [ ] Pre-booking FAQ auto-responder — Captured during: product study
- [ ] CRM for leads who inquired but didn't book — Captured during: product study

---

## Todos

- [ ] Apply for Airbnb Connectivity Partner program (for M2 API integration)
- [ ] Set up Redis instance (required for BullMQ before running locally)
- [ ] Create Supabase project and run migration 001

---

## Preferences

**Model Guidance Shown:** never
