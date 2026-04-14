# Feature: Inicializar Projeto NestJS PMS

## Problem

O repositório está vazio (apenas README e docs). Antes de qualquer feature de negócio poder ser
construída, é necessário estabelecer a fundação técnica completa: estrutura de módulos NestJS,
esquema inicial do banco de dados PostgreSQL via Supabase, configuração tipada de variáveis de
ambiente, infraestrutura de filas BullMQ e os esqueletos (sem lógica de negócio) de todos os
módulos do MVP. Sem essa base, nenhum Builder pode trabalhar de forma paralela ou consistente.

---

## Requirements

| ID      | Requirement                                                                                                     | Acceptance Criteria                                                                                                      |
|---------|-----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| REQ-001 | O projeto NestJS deve ser inicializado com Fastify adapter, configuração global de validação e Swagger           | `npm run start:dev` sobe sem erros; `GET /api/docs` retorna a UI do Swagger                                             |
| REQ-002 | Todas as variáveis de ambiente devem ser declaradas num schema tipado e validadas na inicialização               | Subir sem o `.env` lança erro descritivo por variável faltante; `ConfigService` retorna tipos corretos                   |
| REQ-003 | `SupabaseService` deve ser registrado como provider global e injetável em qualquer módulo                        | Qualquer módulo consegue injetar `SupabaseService` sem importar `DatabaseModule` explicitamente                          |
| REQ-004 | A migração SQL inicial deve criar todas as tabelas do núcleo com constraints, índices e comentários              | Executar `supabase/migrations/001_initial_schema.sql` numa base limpa não retorna erros; todas as tabelas existem        |
| REQ-005 | O módulo `properties` deve expor endpoints CRUD skeleton com DTOs validados                                      | `POST /properties`, `GET /properties`, `GET /properties/:id`, `PATCH /properties/:id`, `DELETE /properties/:id` retornam 501 com corpo `{"status":"not_implemented"}` |
| REQ-006 | O módulo `reservations` deve expor endpoints CRUD skeleton e um endpoint de trigger de sync iCal                 | Endpoints retornam 501; `POST /reservations/sync/:connectionId` retorna 501                                              |
| REQ-007 | O módulo `guests` deve expor endpoints CRUD skeleton                                                             | `POST /guests`, `GET /guests/:id`, `PATCH /guests/:id` retornam 501                                                     |
| REQ-008 | O módulo `channel-manager` deve expor endpoints de gerenciamento de conexões OTA e registrar um BullMQ Queue     | CRUD de conexões retorna 501; `ChannelManagerQueue` é registrado no módulo sem erros de boot                             |
| REQ-009 | O módulo `owner-alerts` deve expor endpoint de listagem e registrar um BullMQ Queue                              | `GET /owner-alerts` retorna 501; queue registrada sem erros                                                              |
| REQ-010 | O módulo `messaging` deve expor um endpoint de envio de mensagem skeleton                                        | `POST /messaging/send` retorna 501                                                                                       |
| REQ-011 | O módulo `financials` deve expor endpoints skeleton para registros financeiros                                    | `POST /financials`, `GET /financials` retornam 501                                                                       |
| REQ-012 | O módulo `cleaning` deve expor endpoints skeleton para tarefas de limpeza                                        | `POST /cleaning-tasks`, `GET /cleaning-tasks` retornam 501                                                               |
| REQ-013 | O `AppModule` deve registrar todos os módulos, `EventEmitterModule`, `ScheduleModule` e `BullModule` globalmente | `npm run build` compila sem erros; todos os módulos aparecem no log de bootstrap do NestJS                               |
| REQ-014 | O projeto deve ter scripts npm padronizados e arquivo `.env.example` documentado                                 | `npm run build`, `npm run lint`, `npm run test` executam sem erros de configuração                                       |

---

## Design

### DB Schema

Arquivo: `supabase/migrations/001_initial_schema.sql`

```sql
-- Enums
CREATE TYPE platform_type AS ENUM ('airbnb', 'booking', 'vrbo', 'direct');
CREATE TYPE reservation_status AS ENUM ('confirmed', 'cancelled', 'pending');
CREATE TYPE checkin_status AS ENUM ('pending', 'docs_sent', 'docs_received', 'approved');
CREATE TYPE document_type AS ENUM ('cpf', 'rg', 'passport', 'other');
CREATE TYPE financial_type AS ENUM ('revenue', 'expense');
CREATE TYPE alert_status AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE message_direction AS ENUM ('in', 'out');
CREATE TYPE message_channel AS ENUM ('whatsapp', 'telegram');
CREATE TYPE cleaning_task_status AS ENUM ('scheduled', 'in_progress', 'done', 'cancelled');
CREATE TYPE plan_type AS ENUM ('starter', 'pro', 'growth');

-- Tenants (hosts)
CREATE TABLE tenants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  whatsapp_number TEXT NOT NULL UNIQUE,
  plan          plan_type NOT NULL DEFAULT 'starter',
  is_active     BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tenants_whatsapp ON tenants(whatsapp_number);

-- Properties
CREATE TABLE properties (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name                 TEXT NOT NULL,
  address              TEXT NOT NULL,
  city                 TEXT NOT NULL,
  state                TEXT NOT NULL,
  capacity             INTEGER NOT NULL DEFAULT 1,
  checkin_time         TIME NOT NULL DEFAULT '15:00',
  checkout_time        TIME NOT NULL DEFAULT '11:00',
  wifi_name            TEXT,
  wifi_password        TEXT,
  access_instructions  TEXT,
  rules                TEXT,
  photo_urls           TEXT[] NOT NULL DEFAULT '{}',
  is_active            BOOLEAN NOT NULL DEFAULT true,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_properties_tenant ON properties(tenant_id);

-- OTA Connections (iCal URLs per platform per property)
CREATE TABLE ota_connections (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id    UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  platform       platform_type NOT NULL,
  ical_url       TEXT,
  api_key        TEXT,
  api_secret     TEXT,
  last_sync_at   TIMESTAMPTZ,
  is_active      BOOLEAN NOT NULL DEFAULT true,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (property_id, platform)
);
CREATE INDEX idx_ota_connections_property ON ota_connections(property_id);

-- Guests
CREATE TABLE guests (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name               TEXT NOT NULL,
  phone              TEXT,
  email              TEXT,
  cpf                TEXT,
  document_type      document_type,
  document_number    TEXT,
  document_photo_url TEXT,
  validated_at       TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_guests_tenant ON guests(tenant_id);
CREATE INDEX idx_guests_phone ON guests(phone);

-- Reservations
CREATE TABLE reservations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id     UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  guest_id        UUID REFERENCES guests(id),
  platform        platform_type NOT NULL,
  external_id     TEXT,
  guest_name      TEXT NOT NULL,
  guest_phone     TEXT,
  guest_email     TEXT,
  checkin_date    DATE NOT NULL,
  checkout_date   DATE NOT NULL,
  nights          INTEGER NOT NULL GENERATED ALWAYS AS (checkout_date - checkin_date) STORED,
  total_amount    NUMERIC(10,2),
  status          reservation_status NOT NULL DEFAULT 'confirmed',
  checkin_status  checkin_status NOT NULL DEFAULT 'pending',
  raw_ical_uid    TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (property_id, external_id),
  CONSTRAINT valid_dates CHECK (checkout_date > checkin_date)
);
CREATE INDEX idx_reservations_property ON reservations(property_id);
CREATE INDEX idx_reservations_checkin_date ON reservations(checkin_date);
CREATE INDEX idx_reservations_status ON reservations(status);

-- Calendar Blocks (manual)
CREATE TABLE calendar_blocks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  start_date  DATE NOT NULL,
  end_date    DATE NOT NULL,
  reason      TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT valid_block_dates CHECK (end_date >= start_date)
);
CREATE INDEX idx_calendar_blocks_property ON calendar_blocks(property_id);

-- Cleaning Tasks
CREATE TABLE cleaning_tasks (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
  property_id    UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  assigned_to    TEXT,
  scheduled_for  TIMESTAMPTZ NOT NULL,
  status         cleaning_task_status NOT NULL DEFAULT 'scheduled',
  notes          TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_cleaning_tasks_property ON cleaning_tasks(property_id);
CREATE INDEX idx_cleaning_tasks_scheduled ON cleaning_tasks(scheduled_for);

-- Financial Records
CREATE TABLE financial_records (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id    UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
  type           financial_type NOT NULL,
  amount         NUMERIC(10,2) NOT NULL,
  category       TEXT NOT NULL,
  description    TEXT,
  record_date    DATE NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_financial_records_property ON financial_records(property_id);
CREATE INDEX idx_financial_records_date ON financial_records(record_date);

-- Owner Alerts Queue
CREATE TABLE owner_alerts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  type           TEXT NOT NULL,
  message        TEXT NOT NULL,
  metadata       JSONB NOT NULL DEFAULT '{}',
  scheduled_for  TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at        TIMESTAMPTZ,
  status         alert_status NOT NULL DEFAULT 'pending',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_owner_alerts_tenant ON owner_alerts(tenant_id);
CREATE INDEX idx_owner_alerts_status ON owner_alerts(status);
CREATE INDEX idx_owner_alerts_scheduled ON owner_alerts(scheduled_for);

-- Message Logs
CREATE TABLE message_logs (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
  tenant_id      UUID REFERENCES tenants(id) ON DELETE SET NULL,
  direction      message_direction NOT NULL,
  channel        message_channel NOT NULL DEFAULT 'whatsapp',
  recipient      TEXT,
  content        TEXT NOT NULL,
  external_id    TEXT,
  sent_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_message_logs_reservation ON message_logs(reservation_id);
CREATE INDEX idx_message_logs_tenant ON message_logs(tenant_id);
```

---

### Module Structure

Every file listed below must be created. Files marked `[skeleton]` contain only the class
declaration, constructor with injected dependencies, and stub methods that throw
`NotImplementedException` or return `{ status: 'not_implemented' }`.

```
src/
  main.ts                                         [bootstrap: Fastify, Swagger, ValidationPipe]
  app.module.ts                                   [root module — registers all modules]

  config/
    configuration.ts                              [typed config factory]
    configuration.schema.ts                       [Joi/class-validator schema for env vars]

  shared/
    database/
      database.module.ts                          [global module exporting SupabaseService]
      supabase.service.ts                         [SupabaseService wrapping @supabase/supabase-js]

  modules/
    properties/
      properties.module.ts
      properties.controller.ts                    [skeleton]
      properties.service.ts                       [skeleton]
      dto/
        create-property.dto.ts
        update-property.dto.ts
        property-response.dto.ts

    reservations/
      reservations.module.ts
      reservations.controller.ts                  [skeleton]
      reservations.service.ts                     [skeleton]
      dto/
        create-reservation.dto.ts
        update-reservation.dto.ts
        reservation-response.dto.ts

    guests/
      guests.module.ts
      guests.controller.ts                        [skeleton]
      guests.service.ts                           [skeleton]
      dto/
        create-guest.dto.ts
        update-guest.dto.ts
        guest-response.dto.ts

    channel-manager/
      channel-manager.module.ts                   [registers BullMQ queue CHANNEL_SYNC]
      channel-manager.controller.ts               [skeleton]
      channel-manager.service.ts                  [skeleton]
      channel-manager.processor.ts               [skeleton BullMQ processor]
      dto/
        create-ota-connection.dto.ts
        update-ota-connection.dto.ts
        ota-connection-response.dto.ts

    owner-alerts/
      owner-alerts.module.ts                      [registers BullMQ queue OWNER_ALERTS]
      owner-alerts.controller.ts                  [skeleton]
      owner-alerts.service.ts                     [skeleton]
      owner-alerts.processor.ts                  [skeleton BullMQ processor]
      dto/
        owner-alert-response.dto.ts

    messaging/
      messaging.module.ts
      messaging.controller.ts                     [skeleton]
      messaging.service.ts                        [skeleton — wraps Evolution API via axios]
      dto/
        send-message.dto.ts
        message-response.dto.ts

    financials/
      financials.module.ts
      financials.controller.ts                    [skeleton]
      financials.service.ts                       [skeleton]
      dto/
        create-financial-record.dto.ts
        financial-record-response.dto.ts

    cleaning/
      cleaning.module.ts
      cleaning.controller.ts                      [skeleton]
      cleaning.service.ts                         [skeleton]
      dto/
        create-cleaning-task.dto.ts
        update-cleaning-task.dto.ts
        cleaning-task-response.dto.ts

supabase/
  migrations/
    001_initial_schema.sql

.env.example
```

---

### API Endpoints

All skeleton endpoints return HTTP 501 with body `{ "status": "not_implemented" }` until
implemented by subsequent features. Swagger decorators must be present on each endpoint.

#### Module: properties — prefix `/properties`

| Method | Path              | Request Body              | Response              | Description                    |
|--------|-------------------|---------------------------|-----------------------|--------------------------------|
| POST   | /properties       | `CreatePropertyDto`       | `PropertyResponseDto` | Create a property              |
| GET    | /properties       | —                         | `PropertyResponseDto[]` | List all properties for tenant |
| GET    | /properties/:id   | —                         | `PropertyResponseDto` | Get a single property          |
| PATCH  | /properties/:id   | `UpdatePropertyDto`       | `PropertyResponseDto` | Update a property              |
| DELETE | /properties/:id   | —                         | `{ success: boolean }` | Soft-delete a property         |

#### Module: reservations — prefix `/reservations`

| Method | Path                              | Request Body               | Response                   | Description                    |
|--------|-----------------------------------|----------------------------|----------------------------|--------------------------------|
| POST   | /reservations                     | `CreateReservationDto`     | `ReservationResponseDto`   | Create a reservation manually  |
| GET    | /reservations                     | query: `propertyId?`       | `ReservationResponseDto[]` | List reservations              |
| GET    | /reservations/:id                 | —                          | `ReservationResponseDto`   | Get a reservation              |
| PATCH  | /reservations/:id                 | `UpdateReservationDto`     | `ReservationResponseDto`   | Update a reservation           |
| POST   | /reservations/sync/:connectionId  | —                          | `{ queued: boolean }`      | Trigger iCal sync for a connection |

#### Module: guests — prefix `/guests`

| Method | Path          | Request Body        | Response             | Description        |
|--------|---------------|---------------------|----------------------|--------------------|
| POST   | /guests       | `CreateGuestDto`    | `GuestResponseDto`   | Create guest       |
| GET    | /guests/:id   | —                   | `GuestResponseDto`   | Get guest          |
| PATCH  | /guests/:id   | `UpdateGuestDto`    | `GuestResponseDto`   | Update guest       |

#### Module: channel-manager — prefix `/channel-manager`

| Method | Path                          | Request Body                  | Response                      | Description                        |
|--------|-------------------------------|-------------------------------|-------------------------------|------------------------------------|
| POST   | /channel-manager/connections  | `CreateOtaConnectionDto`      | `OtaConnectionResponseDto`    | Add OTA connection for a property  |
| GET    | /channel-manager/connections  | query: `propertyId?`          | `OtaConnectionResponseDto[]`  | List OTA connections               |
| PATCH  | /channel-manager/connections/:id | `UpdateOtaConnectionDto`   | `OtaConnectionResponseDto`    | Update an OTA connection           |
| DELETE | /channel-manager/connections/:id | —                          | `{ success: boolean }`        | Remove an OTA connection           |

#### Module: owner-alerts — prefix `/owner-alerts`

| Method | Path             | Request Body | Response                    | Description             |
|--------|------------------|--------------|-----------------------------|-------------------------|
| GET    | /owner-alerts    | query: `status?`, `page?`, `limit?` | `OwnerAlertResponseDto[]` | List alerts for tenant |

#### Module: messaging — prefix `/messaging`

| Method | Path              | Request Body       | Response               | Description          |
|--------|-------------------|--------------------|------------------------|----------------------|
| POST   | /messaging/send   | `SendMessageDto`   | `MessageResponseDto`   | Send a WhatsApp message |

#### Module: financials — prefix `/financials`

| Method | Path           | Request Body                   | Response                        | Description              |
|--------|----------------|--------------------------------|---------------------------------|--------------------------|
| POST   | /financials    | `CreateFinancialRecordDto`     | `FinancialRecordResponseDto`    | Create financial record  |
| GET    | /financials    | query: `propertyId?`, `type?`  | `FinancialRecordResponseDto[]`  | List financial records   |

#### Module: cleaning — prefix `/cleaning-tasks`

| Method | Path                  | Request Body               | Response                    | Description              |
|--------|-----------------------|----------------------------|-----------------------------|--------------------------|
| POST   | /cleaning-tasks       | `CreateCleaningTaskDto`    | `CleaningTaskResponseDto`   | Create cleaning task     |
| GET    | /cleaning-tasks       | query: `propertyId?`       | `CleaningTaskResponseDto[]` | List cleaning tasks      |
| PATCH  | /cleaning-tasks/:id   | `UpdateCleaningTaskDto`    | `CleaningTaskResponseDto`   | Update cleaning task     |

---

### Config Keys

All keys must be present in `.env.example` with placeholder values and inline comments.

| Key                          | Type    | Required | Description                                          |
|------------------------------|---------|----------|------------------------------------------------------|
| `NODE_ENV`                   | string  | yes      | `development` / `production` / `test`                |
| `PORT`                       | number  | no       | HTTP port (default: 3000)                            |
| `SUPABASE_URL`               | string  | yes      | Supabase project URL                                 |
| `SUPABASE_SERVICE_ROLE_KEY`  | string  | yes      | Service role key (bypasses RLS — backend only)       |
| `SUPABASE_ANON_KEY`          | string  | yes      | Anon key for public operations                       |
| `REDIS_HOST`                 | string  | yes      | Redis host for BullMQ                                |
| `REDIS_PORT`                 | number  | no       | Redis port (default: 6379)                           |
| `REDIS_PASSWORD`             | string  | no       | Redis password if set                                |
| `EVOLUTION_API_URL`          | string  | yes      | Base URL of Evolution API instance                   |
| `EVOLUTION_API_KEY`          | string  | yes      | API key for Evolution API                            |
| `EVOLUTION_INSTANCE_NAME`    | string  | yes      | WhatsApp instance name in Evolution API              |
| `CLAUDE_API_KEY`             | string  | yes      | Anthropic API key                                    |
| `SWAGGER_ENABLED`            | boolean | no       | Enable Swagger UI (default: true in non-production)  |
| `LOG_LEVEL`                  | string  | no       | `error` / `warn` / `log` / `debug` (default: `log`)  |

---

### Async Jobs (BullMQ Queues)

At this stage only queue registration is required — no processors contain logic yet.

| Queue Name        | Module           | Processor File                             | Purpose                                |
|-------------------|------------------|--------------------------------------------|----------------------------------------|
| `channel-sync`    | channel-manager  | `channel-manager.processor.ts`             | iCal fetch and diff per connection     |
| `owner-alerts`    | owner-alerts     | `owner-alerts.processor.ts`               | Send WhatsApp alert to host            |

Both queues connect to the shared Redis config via `BullModule.forRootAsync`.

---

## Tasks

```
TASK-001: [Config] Create .env.example and configuration factory
  Depends on: —
  Files:
    .env.example
    src/config/configuration.ts
  Done when: All 14 config keys are present in .env.example with comments;
             configuration.ts exports a typed factory function returning a
             nested config object; no TypeScript errors.

TASK-002: [Config] Create Joi validation schema for environment variables
  Depends on: TASK-001
  Files:
    src/config/configuration.schema.ts
  Done when: Schema validates all required keys; `npm run start:dev` without
             SUPABASE_URL throws a descriptive Joi validation error and exits.

TASK-003: [Shared] Create DatabaseModule and SupabaseService
  Depends on: TASK-001
  Files:
    src/shared/database/database.module.ts
    src/shared/database/supabase.service.ts
  Done when: DatabaseModule is marked @Global(); SupabaseService is exported;
             service instantiates a SupabaseClient using config values;
             no TypeScript errors.

TASK-004: [DB] Write initial SQL migration
  Depends on: —
  Files:
    supabase/migrations/001_initial_schema.sql
  Done when: All 10 tables and all enums are created; all foreign keys and
             indexes are present; running against a clean Postgres instance
             produces no errors.

TASK-005: [Core] Bootstrap main.ts with Fastify, Swagger and ValidationPipe
  Depends on: TASK-002, TASK-003
  Files:
    src/main.ts
  Done when: App boots with Fastify adapter; `GET /api/docs` returns Swagger UI
             HTML; GlobalValidationPipe is registered with whitelist:true and
             forbidNonWhitelisted:true.

TASK-006: [Module] Scaffold properties module — DTOs, service, controller
  Depends on: TASK-003
  Files:
    src/modules/properties/dto/create-property.dto.ts
    src/modules/properties/dto/update-property.dto.ts
    src/modules/properties/dto/property-response.dto.ts
  Done when: All DTO fields have class-validator decorators; DTOs compile without
             errors; ApiProperty decorators are present for Swagger.

TASK-007: [Module] Scaffold properties controller and service
  Depends on: TASK-006
  Files:
    src/modules/properties/properties.service.ts
    src/modules/properties/properties.controller.ts
  Done when: All 5 endpoints are declared with correct HTTP methods and paths;
             each returns { status: 'not_implemented' } with HTTP 501;
             Swagger decorators present; no TypeScript errors.

TASK-008: [Module] Create PropertiesModule and register in AppModule
  Depends on: TASK-007
  Files:
    src/modules/properties/properties.module.ts
    src/app.module.ts
  Done when: PropertiesModule is imported in AppModule; app boots; all 5
             property routes appear in Swagger UI.

TASK-009: [Module] Scaffold reservations module (DTOs + service + controller + module)
  Depends on: TASK-003
  Files:
    src/modules/reservations/dto/create-reservation.dto.ts
    src/modules/reservations/dto/update-reservation.dto.ts
    src/modules/reservations/dto/reservation-response.dto.ts
  Done when: DTOs compile; all fields have class-validator and ApiProperty
             decorators.

TASK-010: [Module] Scaffold reservations service and controller
  Depends on: TASK-009
  Files:
    src/modules/reservations/reservations.service.ts
    src/modules/reservations/reservations.controller.ts
  Done when: 5 endpoints (including sync trigger) declared; all return 501;
             no TypeScript errors.

TASK-011: [Module] Create ReservationsModule and register in AppModule
  Depends on: TASK-010
  Files:
    src/modules/reservations/reservations.module.ts
    src/app.module.ts
  Done when: Module imported; all 5 reservation routes appear in Swagger UI.

TASK-012: [Module] Scaffold guests module (DTOs + service + controller + module)
  Depends on: TASK-003
  Files:
    src/modules/guests/dto/create-guest.dto.ts
    src/modules/guests/dto/update-guest.dto.ts
    src/modules/guests/dto/guest-response.dto.ts
  Done when: DTOs compile; all 3 guest endpoints return 501; module registered
             in AppModule.

TASK-013: [Module] Scaffold guests service, controller, and module
  Depends on: TASK-012
  Files:
    src/modules/guests/guests.service.ts
    src/modules/guests/guests.controller.ts
    src/modules/guests/guests.module.ts
  Done when: Module registered in AppModule; 3 routes in Swagger UI; no errors.

TASK-014: [Module] Scaffold channel-manager module with BullMQ queue
  Depends on: TASK-003
  Files:
    src/modules/channel-manager/dto/create-ota-connection.dto.ts
    src/modules/channel-manager/dto/update-ota-connection.dto.ts
    src/modules/channel-manager/dto/ota-connection-response.dto.ts
  Done when: DTOs compile with all OTA connection fields and decorators.

TASK-015: [Module] Scaffold channel-manager service, controller, processor, and module
  Depends on: TASK-014
  Files:
    src/modules/channel-manager/channel-manager.service.ts
    src/modules/channel-manager/channel-manager.controller.ts
    src/modules/channel-manager/channel-manager.processor.ts
  Done when: 4 endpoints return 501; `channel-sync` BullMQ queue registered;
             processor class has `@Processor('channel-sync')` decorator; no errors.

TASK-016: [Module] Create ChannelManagerModule and register in AppModule
  Depends on: TASK-015
  Files:
    src/modules/channel-manager/channel-manager.module.ts
    src/app.module.ts
  Done when: Module imported; 4 channel-manager routes visible in Swagger UI;
             queue boots without Redis connection errors when Redis is available.

TASK-017: [Module] Scaffold owner-alerts module with BullMQ queue
  Depends on: TASK-003
  Files:
    src/modules/owner-alerts/dto/owner-alert-response.dto.ts
    src/modules/owner-alerts/owner-alerts.service.ts
    src/modules/owner-alerts/owner-alerts.controller.ts
  Done when: GET /owner-alerts returns 501; `owner-alerts` BullMQ queue
             registered; no TypeScript errors.

TASK-018: [Module] Create OwnerAlertsModule and register in AppModule
  Depends on: TASK-017
  Files:
    src/modules/owner-alerts/owner-alerts.module.ts
    src/modules/owner-alerts/owner-alerts.processor.ts
    src/app.module.ts
  Done when: Module imported; processor has `@Processor('owner-alerts')`;
             route appears in Swagger UI.

TASK-019: [Module] Scaffold messaging module
  Depends on: TASK-003
  Files:
    src/modules/messaging/dto/send-message.dto.ts
    src/modules/messaging/dto/message-response.dto.ts
    src/modules/messaging/messaging.service.ts
  Done when: DTOs compile; service has `sendMessage` method stub that returns
             not_implemented; axios is imported for future Evolution API calls.

TASK-020: [Module] Create messaging controller and module, register in AppModule
  Depends on: TASK-019
  Files:
    src/modules/messaging/messaging.controller.ts
    src/modules/messaging/messaging.module.ts
    src/app.module.ts
  Done when: POST /messaging/send returns 501; module registered; route in
             Swagger UI.

TASK-021: [Module] Scaffold financials module
  Depends on: TASK-003
  Files:
    src/modules/financials/dto/create-financial-record.dto.ts
    src/modules/financials/dto/financial-record-response.dto.ts
    src/modules/financials/financials.service.ts
  Done when: DTOs compile; service stubs present.

TASK-022: [Module] Create financials controller and module, register in AppModule
  Depends on: TASK-021
  Files:
    src/modules/financials/financials.controller.ts
    src/modules/financials/financials.module.ts
    src/app.module.ts
  Done when: POST /financials and GET /financials return 501; Swagger UI shows
             both routes.

TASK-023: [Module] Scaffold cleaning module
  Depends on: TASK-003
  Files:
    src/modules/cleaning/dto/create-cleaning-task.dto.ts
    src/modules/cleaning/dto/update-cleaning-task.dto.ts
    src/modules/cleaning/dto/cleaning-task-response.dto.ts
  Done when: DTOs compile with all fields and decorators.

TASK-024: [Module] Create cleaning service, controller, and module, register in AppModule
  Depends on: TASK-023
  Files:
    src/modules/cleaning/cleaning.service.ts
    src/modules/cleaning/cleaning.controller.ts
    src/modules/cleaning/cleaning.module.ts
  Done when: POST /cleaning-tasks, GET /cleaning-tasks, PATCH /cleaning-tasks/:id
             return 501; module registered in AppModule; routes in Swagger UI.

TASK-025: [Core] Finalize AppModule with EventEmitter, Schedule, and BullMQ global config
  Depends on: TASK-016, TASK-018, TASK-020, TASK-022, TASK-024
  Files:
    src/app.module.ts
  Done when: AppModule imports EventEmitterModule.forRoot(), ScheduleModule.forRoot(),
             BullModule.forRootAsync() pointing to Redis config; `npm run build`
             compiles with zero TypeScript errors; `npm run start:dev` logs all
             module bootstraps without errors.

TASK-026: [Infra] Add package.json scripts and verify project builds
  Depends on: TASK-025
  Files:
    package.json
    tsconfig.json
  Done when: `npm run build` exits 0; `npm run lint` exits 0; `npm run test`
             exits 0 (no tests yet, Jest finds 0 suites); nest-cli.json present
             with correct sourceRoot.
```

---

## Out of Scope

The following items are explicitly NOT part of this initialization task:

- Any real business logic in services (all methods remain stubs)
- Authentication and authorization (JWT, guards, tenant middleware)
- iCal parsing and sync logic (belongs to a future channel-manager feature)
- WhatsApp message flows and Evolution API integration (messaging module is skeleton only)
- BullMQ job processors with actual logic (only class scaffolds)
- NestJS scheduler jobs (`@Cron` decorators with logic)
- Frontend (Next.js) — entirely out of scope for this task
- Supabase Row Level Security (RLS) policies
- Supabase Storage configuration for document/photo uploads
- Claude API integration and AI agent logic
- Smart lock integrations (TTLock, Yale)
- Financial reports beyond the skeleton endpoint
- Multi-tenant isolation logic at the service layer
- Docker / docker-compose setup
- CI/CD pipeline configuration
- Unit or integration tests (test files will be empty stubs)
- Data seeding scripts
