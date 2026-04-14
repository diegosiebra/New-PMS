# New PMS

**Vision:** A WhatsApp-first Property Management System that works proactively for individual hosts in Brazil — alerting them about what needs to be done instead of waiting for them to log in.
**For:** Individual hosts with 1–10 short-term rental properties in Brazil (Airbnb, Booking.com, VRBO)
**Solves:** Existing tools (Stays.net, Hiper) are reactive, complex, and expensive for small hosts. Hosts spend time managing tools instead of the tools managing the work.

## Goals

- **Primary:** Host can connect Airbnb + Booking.com via iCal, receive WhatsApp alerts for every key event, and complete guest check-in digitally — all within 10 minutes of onboarding
- **Secondary:** Reduce host manual work by 80% through proactive automation (no login required for daily operations)
- **Metric:** 20 paying hosts in month 1, churn < 5%/month, NPS > 50

## Tech Stack

**Core:**

- Framework: NestJS 10 (modular monolith)
- Language: TypeScript 5
- Database: PostgreSQL via Supabase
- Runtime: Node.js 24

**Key dependencies:**
- `@nestjs/bull` + BullMQ — async job queue (iCal sync, alert dispatch)
- `@nestjs/event-emitter` — cross-module events (reservation.created → alert + cleaning)
- `@supabase/supabase-js` — database client
- `node-ical` — iCal parsing for OTA sync
- `axios` — Evolution API HTTP calls (WhatsApp)
- Claude API (`claude-haiku-4-5`) — AI agents for guest automation

## Scope

**v1 (MVP) includes:**

- Property CRUD with iCal connection per OTA platform
- Automated iCal sync (Airbnb, Booking.com, VRBO) every 15 min via BullMQ
- Guest check-in digital flow via WhatsApp (document collection)
- Proactive owner alerts via WhatsApp: new reservation, check-in pending, checkout today, weekly report
- Automatic cleaning task creation on checkout
- Basic financial records (revenue + expense per property)
- REST API with Swagger docs
- Supabase schema migration

**Explicitly out of scope (v1):**

- Frontend / dashboard UI (API-only)
- Authentication / multi-tenant auth guards (TEMP_TENANT_ID placeholder)
- Airbnb / Booking.com official API (iCal only)
- Telegram support
- NF-e / PIX / payment processing
- Smart lock integrations
- Revenue management / dynamic pricing
- Mobile app / PWA

## Constraints

- Timeline: MVP in 10–12 weeks
- Technical: Must work with Evolution API self-hosted instance; Supabase for DB (no self-hosted Postgres needed)
- Resources: Solo or small team — keep complexity low, no premature abstractions
