# Roadmap

**Current Milestone:** M1 — MVP Core
**Status:** Planning

---

## M1 — MVP Core (Weeks 1–12)

**Goal:** Host connects Airbnb + Booking via iCal, receives WhatsApp alerts, guests do digital check-in
**Target:** First paying customer onboarded

### Features

**Project Bootstrap** - PLANNED
- NestJS project scaffold (package.json, tsconfig, nest-cli)
- App module with ConfigModule, BullMQ, EventEmitter, Schedule
- Supabase database schema (migration 001)
- Shared DatabaseModule (SupabaseService)
- .env.example with all required variables

**Properties** - PLANNED
- CRUD for properties (name, address, capacity, check-in/out times, WiFi, access instructions, rules, photos)
- OTA connection management per property (iCal URL per platform)
- Calendar blocks (manual date blocking)

**Channel Manager** - PLANNED
- iCal sync engine (node-ical parsing)
- BullMQ processor: sync per property, detect new/cancelled reservations
- Scheduled cron every 15 min for all active connections
- Manual trigger endpoint per property

**Reservations** - PLANNED
- Reservation model (platform, external_id, guest info, dates, status, checkin_status)
- Create / list / get endpoints
- Event emission on create → triggers owner alert + cleaning task

**Guests** - PLANNED
- Guest upsert by phone
- Document storage (type, number, photo URL)
- Find by phone (used by WhatsApp flows)

**Messaging** - PLANNED
- Evolution API abstraction (sendWhatsApp)
- Error handling with retry

**Owner Alerts** - PLANNED
- BullMQ queue: dispatch and schedule alerts
- Processor: fetch tenant WhatsApp + send via MessagingService
- Message templates: new_reservation, checkin_pending, checkin_today, checkout_today, calendar_idle, weekly_report
- Event listener: reservation.created → new_reservation alert

**Cleaning** - PLANNED
- Auto-create cleaning task on reservation.created (scheduled for checkout date)
- List tasks by property
- Mark task as done

**Financials** - PLANNED
- Create revenue/expense records
- Monthly summary (revenue, expenses, net) with optional property filter

---

## M2 — Operations & Reliability (Weeks 13–24)

**Goal:** Production-ready: auth, multi-tenant isolation, monitoring, full check-in flow

### Features

**Authentication & Multi-tenancy** - PLANNED
- JWT auth guard
- Tenant resolution from JWT (replace TEMP_TENANT_ID)
- Row-level security on Supabase

**WhatsApp Check-in Flow** - PLANNED
- Webhook endpoint for inbound WhatsApp messages
- Conversation state machine per guest+reservation
- D-3 welcome message dispatch
- Document collection + validation via Claude API
- Access instructions delivery on approval

**Proactive Scheduler** - PLANNED
- Daily job: D-1 checkin_pending alerts
- Daily job: checkin_today / checkout_today alerts
- Monday 9am: weekly report generation
- Calendar idle detection (7 days without reservation)

**Monitoring & Observability** - PLANNED
- BullMQ dashboard (Bull Board)
- Structured logging (Pino)
- Health check endpoint

---

## M3 — Growth (Weeks 25+)

**Goal:** Conversion features, revenue management, direct booking

### Features

**Direct Booking Engine** - PLANNED
**PIX Payment Integration** - PLANNED
**Revenue Management (AI pricing)** - PLANNED
**Airbnb / Booking.com Official API** - PLANNED
**Smart Lock Integration (TTLock)** - PLANNED
**Telegram Channel** - PLANNED
**NF-e Emission** - PLANNED
**Owner Portal (multi-property managers)** - PLANNED

---

## Future Considerations

- Mobile app / PWA
- OTA regional integrations (Decolar, AlugueTemporada)
- Competitor price monitoring
- Upsell automation (early check-in, late checkout)
