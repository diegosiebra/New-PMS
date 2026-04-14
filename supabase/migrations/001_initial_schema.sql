-- Migration: 001_initial_schema
-- Description: Initial database schema for PMS (Property Management System)
-- Tables are created in FK dependency order

-- ─── tenants ──────────────────────────────────────────────────────────────────
CREATE TABLE tenants (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name               TEXT NOT NULL,
  whatsapp_number    TEXT NOT NULL UNIQUE,
  evolution_instance TEXT,
  plan               TEXT NOT NULL DEFAULT 'starter' CHECK (plan IN ('starter', 'pro', 'growth')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─── properties ───────────────────────────────────────────────────────────────
CREATE TABLE properties (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name                 TEXT NOT NULL,
  address              TEXT,
  capacity             INTEGER,
  checkin_time         TIME,
  checkout_time        TIME,
  wifi_name            TEXT,
  wifi_password        TEXT,
  access_instructions  TEXT,
  rules                TEXT,
  photos               TEXT[] NOT NULL DEFAULT '{}',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_properties_tenant_id ON properties(tenant_id);

-- ─── ota_connections ──────────────────────────────────────────────────────────
CREATE TABLE ota_connections (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id  UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  platform     TEXT NOT NULL CHECK (platform IN ('airbnb', 'booking', 'vrbo', 'direct')),
  ical_url     TEXT,
  api_key      TEXT,         -- SECURITY: encrypt before production
  api_secret   TEXT,         -- SECURITY: encrypt before production
  last_sync_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(property_id, platform)
);

CREATE INDEX idx_ota_connections_tenant_id ON ota_connections(tenant_id);
CREATE INDEX idx_ota_connections_property_id ON ota_connections(property_id);

-- ─── guests ───────────────────────────────────────────────────────────────────
-- LGPD NOTE: cpf, document_number, and document_photo_url contain personal data
-- protected under Brazilian LGPD. These columns MUST be encrypted at the
-- application layer before production deployment. Encryption deferred to M2.
CREATE TABLE guests (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name               TEXT,
  phone              TEXT NOT NULL,
  email              TEXT,
  cpf                TEXT,       -- LGPD: encrypt before production
  document_type      TEXT,
  document_number    TEXT,       -- LGPD: encrypt before production
  document_photo_url TEXT,       -- LGPD: encrypt before production
  validated_at       TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, phone)
);

CREATE INDEX idx_guests_tenant_id ON guests(tenant_id);

-- ─── reservations ─────────────────────────────────────────────────────────────
CREATE TABLE reservations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  property_id     UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  guest_id        UUID REFERENCES guests(id),
  platform        TEXT NOT NULL CHECK (platform IN ('airbnb', 'booking', 'vrbo', 'direct')),
  external_id     TEXT NOT NULL,
  guest_name      TEXT,
  guest_phone     TEXT,
  guest_email     TEXT,
  checkin_date    DATE NOT NULL,
  checkout_date   DATE NOT NULL,
  total_amount    NUMERIC(10, 2),
  nights          INTEGER CHECK (nights > 0),
  status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
  checkin_status  TEXT NOT NULL DEFAULT 'pending' CHECK (checkin_status IN ('pending', 'docs_requested', 'docs_received', 'approved')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(property_id, platform, external_id),
  CONSTRAINT chk_reservation_dates CHECK (checkout_date > checkin_date)
);

CREATE INDEX idx_reservations_tenant_id ON reservations(tenant_id);
CREATE INDEX idx_reservations_property_id ON reservations(property_id);
CREATE INDEX idx_reservations_checkin_date ON reservations(checkin_date);
CREATE INDEX idx_reservations_checkout_date ON reservations(checkout_date);

-- ─── calendar_blocks ──────────────────────────────────────────────────────────
CREATE TABLE calendar_blocks (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id  UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  reason       TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_date >= start_date)
);

CREATE INDEX idx_calendar_blocks_property_id ON calendar_blocks(property_id);

-- ─── cleaning_tasks ───────────────────────────────────────────────────────────
CREATE TABLE cleaning_tasks (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
  assigned_to    TEXT,
  scheduled_for  DATE NOT NULL,
  status         TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done')),
  notes          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cleaning_tasks_reservation_id ON cleaning_tasks(reservation_id);
CREATE INDEX idx_cleaning_tasks_scheduled_for ON cleaning_tasks(scheduled_for);

-- ─── financial_records ────────────────────────────────────────────────────────
CREATE TABLE financial_records (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  property_id    UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  reservation_id UUID REFERENCES reservations(id),
  type           TEXT NOT NULL CHECK (type IN ('revenue', 'expense')),
  amount         NUMERIC(10, 2) NOT NULL,
  category       TEXT,
  date           DATE NOT NULL,
  notes          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_financial_records_tenant_id ON financial_records(tenant_id);
CREATE INDEX idx_financial_records_property_id ON financial_records(property_id);
CREATE INDEX idx_financial_records_date ON financial_records(date);

-- ─── message_logs ─────────────────────────────────────────────────────────────
CREATE TABLE message_logs (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID REFERENCES reservations(id),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  direction      TEXT NOT NULL CHECK (direction IN ('in', 'out')),
  channel        TEXT NOT NULL DEFAULT 'whatsapp' CHECK (channel IN ('whatsapp', 'telegram')),
  phone          TEXT NOT NULL,
  content        TEXT NOT NULL,
  sent_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_message_logs_tenant_id ON message_logs(tenant_id);
CREATE INDEX idx_message_logs_reservation_id ON message_logs(reservation_id);
CREATE INDEX idx_message_logs_sent_at ON message_logs(sent_at);
