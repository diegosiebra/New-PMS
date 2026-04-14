# Feature: Project Bootstrap

## Problem

Before any domain feature can be built, the NestJS project must exist as a runnable, correctly wired skeleton. Without this foundation, every subsequent task (Properties, Channel Manager, Reservations, etc.) has nowhere to land. The bootstrap establishes the module graph, environment contract, database schema, and tooling configuration that all other features depend on. It is the single output that transforms an empty repository into a deployable, testable application.

---

## Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | `package.json` lists all runtime and dev dependencies with pinned major versions and provides scripts: `start:dev`, `build`, `test`, `lint`, `format` | `npm install` completes without errors; each script runs without "command not found" |
| REQ-002 | TypeScript is configured with `strict: true`, `paths` aliases for `@shared/*`, `@modules/*`, `@config/*`, and `rootDir: src` | `tsc --noEmit` exits 0 on an empty `src/main.ts`; path aliases resolve in both IDE and build |
| REQ-003 | `nest-cli.json` declares `src` as source root and `dist` as output path, with `deleteOutDir: true` | `npm run build` produces a `dist/` folder and `npm run start:prod` starts the app |
| REQ-004 | `.eslintrc.js` enforces `@typescript-eslint` rules: no explicit `any`, no unused variables, consistent return | `npm run lint` exits 0 on the generated scaffold; exits non-zero if `any` is introduced |
| REQ-005 | `.prettierrc` sets `singleQuote: true`, `trailingComma: "all"`, `printWidth: 100`, `tabWidth: 2` | `npm run format` re-formats files; no diff on already-formatted source |
| REQ-006 | `.env.example` documents every environment variable the app reads, with inline comments | All variables listed in the table under Design > Config Groups are present; no variable is read by the app without a corresponding entry |
| REQ-007 | `.gitignore` excludes `node_modules/`, `dist/`, `.env`, `coverage/` | A freshly cloned repo with those paths present shows them as untracked-ignored by git |
| REQ-008 | `src/config/configuration.ts` exports a `ConfigModule.forRoot()` factory that maps env vars into typed config groups (`supabase`, `redis`, `evolution`, `anthropic`, `ical`) | `ConfigService.get('supabase.url')` returns the value of `SUPABASE_URL` at runtime |
| REQ-009 | `SupabaseService` initialises a `SupabaseClient` using service-role key on module init and exposes it via a `get db()` property | `supabaseService.db.from('tenants').select()` executes without throwing |
| REQ-010 | `DatabaseModule` is a `@Global()` module that provides and exports `SupabaseService` | Any module in `app.module.ts` can inject `SupabaseService` without importing `DatabaseModule` directly |
| REQ-011 | `AppModule` imports: `ConfigModule` (global), `EventEmitterModule.forRoot()`, `ScheduleModule.forRoot()`, `BullModule.forRootAsync()` (reads Redis config from `ConfigService`), `DatabaseModule`, and all 8 domain modules as empty stubs | `npm run start:dev` starts without error; `GET /` returns 404 (no routes yet, but app is up) |
| REQ-012 | `main.ts` bootstraps with Fastify adapter, applies `ValidationPipe` with `whitelist: true`, `forbidNonWhitelisted: true`, `transform: true`, enables URI versioning (default version `'1'`), enables CORS, sets up Swagger at `/docs`, and listens on `PORT` | `GET /docs` returns the Swagger UI HTML; `PORT=3001 node dist/main` starts on 3001 |
| REQ-013 | `supabase/migrations/001_initial_schema.sql` contains the full DDL for all 9 tables with correct column types, NOT NULL constraints, foreign keys, unique constraints, and indexes | Running the migration on a blank Supabase project succeeds without errors; all 9 tables are created |
| REQ-014 | Each of the 8 domain modules exists as a stub (`module.ts` only, empty providers/controllers arrays) wired into `AppModule` | Removing any module import from `AppModule` causes a TypeScript error for the missing symbol |

---

## Design

### File Structure

```
/                                   ← repo root
├── package.json
├── tsconfig.json
├── tsconfig.build.json
├── nest-cli.json
├── .eslintrc.js
├── .prettierrc
├── .env.example
├── .gitignore
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
└── src/
    ├── main.ts
    ├── app.module.ts
    ├── config/
    │   └── configuration.ts
    ├── shared/
    │   └── database/
    │       ├── supabase.service.ts
    │       └── database.module.ts
    └── modules/
        ├── properties/
        │   └── properties.module.ts
        ├── reservations/
        │   └── reservations.module.ts
        ├── guests/
        │   └── guests.module.ts
        ├── channel-manager/
        │   └── channel-manager.module.ts
        ├── owner-alerts/
        │   └── owner-alerts.module.ts
        ├── messaging/
        │   └── messaging.module.ts
        ├── financials/
        │   └── financials.module.ts
        └── cleaning/
            └── cleaning.module.ts
```

### Dependencies

**Runtime dependencies (exact packages):**

| Package | Version | Purpose |
|---------|---------|---------|
| `@nestjs/common` | `^10.0.0` | Core NestJS framework |
| `@nestjs/core` | `^10.0.0` | NestJS core runtime |
| `@nestjs/platform-fastify` | `^10.0.0` | Fastify HTTP adapter |
| `@nestjs/config` | `^3.0.0` | ConfigModule / ConfigService |
| `@nestjs/bull` | `^10.0.0` | BullMQ integration |
| `@nestjs/event-emitter` | `^2.0.0` | EventEmitter2 integration |
| `@nestjs/schedule` | `^4.0.0` | Cron scheduler |
| `@nestjs/swagger` | `^7.0.0` | OpenAPI / Swagger UI |
| `@supabase/supabase-js` | `^2.0.0` | Supabase PostgreSQL client |
| `bullmq` | `^5.0.0` | BullMQ queue engine |
| `class-validator` | `^0.14.0` | DTO validation decorators |
| `class-transformer` | `^0.5.0` | DTO transformation |
| `node-ical` | `^0.18.0` | iCal feed parsing |
| `axios` | `^1.6.0` | HTTP client for Evolution API |
| `fastify` | `^4.0.0` | Fastify web server |
| `reflect-metadata` | `^0.1.13` | Decorator metadata |
| `rxjs` | `^7.8.0` | Reactive extensions (NestJS peer) |

**Dev dependencies (exact packages):**

| Package | Version | Purpose |
|---------|---------|---------|
| `@nestjs/cli` | `^10.0.0` | NestJS CLI |
| `@nestjs/testing` | `^10.0.0` | NestJS test utilities |
| `@types/node` | `^20.0.0` | Node.js types |
| `@typescript-eslint/eslint-plugin` | `^7.0.0` | TypeScript ESLint rules |
| `@typescript-eslint/parser` | `^7.0.0` | TypeScript ESLint parser |
| `eslint` | `^8.0.0` | ESLint core |
| `jest` | `^29.0.0` | Test runner |
| `ts-jest` | `^29.0.0` | TypeScript Jest transformer |
| `ts-node` | `^10.0.0` | TypeScript Node runner |
| `typescript` | `^5.0.0` | TypeScript compiler |
| `prettier` | `^3.0.0` | Code formatter |
| `@types/node-ical` | `^0.16.0` | Types for node-ical |

**`package.json` scripts:**

```json
{
  "start:dev": "nest start --watch",
  "start:prod": "node dist/main",
  "build": "nest build",
  "test": "jest",
  "test:watch": "jest --watch",
  "test:cov": "jest --coverage",
  "lint": "eslint \"{src,apps,libs,test}/**/*.ts\" --fix",
  "format": "prettier --write \"src/**/*.ts\""
}
```

### DB Schema

Full DDL for `supabase/migrations/001_initial_schema.sql`. Tables must be created in dependency order (no forward FK references).

**Table: `tenants`**
```sql
CREATE TABLE tenants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  whatsapp_number TEXT NOT NULL UNIQUE,
  evolution_instance TEXT,
  plan          TEXT NOT NULL DEFAULT 'starter',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Table: `properties`**
```sql
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
```

**Table: `ota_connections`**
```sql
CREATE TABLE ota_connections (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id  UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  platform     TEXT NOT NULL CHECK (platform IN ('airbnb', 'booking', 'vrbo', 'direct')),
  ical_url     TEXT,
  api_key      TEXT,
  api_secret   TEXT,
  last_sync_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(property_id, platform)
);
CREATE INDEX idx_ota_connections_tenant_id ON ota_connections(tenant_id);
CREATE INDEX idx_ota_connections_property_id ON ota_connections(property_id);
```

**Table: `guests`**
```sql
CREATE TABLE guests (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name               TEXT,
  phone              TEXT NOT NULL,
  email              TEXT,
  cpf                TEXT,
  document_type      TEXT,
  document_number    TEXT,
  document_photo_url TEXT,
  validated_at       TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, phone)
);
CREATE INDEX idx_guests_tenant_id ON guests(tenant_id);
```

**Table: `reservations`**
```sql
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
  nights          INTEGER,
  status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
  checkin_status  TEXT NOT NULL DEFAULT 'pending' CHECK (checkin_status IN ('pending', 'docs_requested', 'docs_received', 'approved')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(property_id, platform, external_id)
);
CREATE INDEX idx_reservations_tenant_id ON reservations(tenant_id);
CREATE INDEX idx_reservations_property_id ON reservations(property_id);
CREATE INDEX idx_reservations_checkin_date ON reservations(checkin_date);
CREATE INDEX idx_reservations_checkout_date ON reservations(checkout_date);
```

**Table: `calendar_blocks`**
```sql
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
```

**Table: `cleaning_tasks`**
```sql
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
```

**Table: `financial_records`**
```sql
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
```

**Table: `message_logs`**
```sql
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
```

### Config Groups

`src/config/configuration.ts` exports a factory function for `ConfigModule.forRoot({ load: [configuration] })`.

**Environment variables and their config paths:**

| Env Var | Config Path | Type | Required | Default |
|---------|-------------|------|----------|---------|
| `PORT` | `app.port` | number | no | `3000` |
| `SUPABASE_URL` | `supabase.url` | string | yes | — |
| `SUPABASE_SERVICE_KEY` | `supabase.serviceKey` | string | yes | — |
| `DATABASE_URL` | `supabase.databaseUrl` | string | no | — |
| `REDIS_HOST` | `redis.host` | string | no | `localhost` |
| `REDIS_PORT` | `redis.port` | number | no | `6379` |
| `REDIS_PASSWORD` | `redis.password` | string | no | `""` |
| `EVOLUTION_API_URL` | `evolution.apiUrl` | string | yes | — |
| `EVOLUTION_API_KEY` | `evolution.apiKey` | string | yes | — |
| `ANTHROPIC_API_KEY` | `anthropic.apiKey` | string | yes | — |
| `ANTHROPIC_MODEL` | `anthropic.model` | string | no | `claude-haiku-4-5` |
| `ICAL_SYNC_INTERVAL_MINUTES` | `ical.syncIntervalMinutes` | number | no | `15` |

The factory function returns a plain object matching this shape:
```typescript
export default () => ({
  app: { port: parseInt(process.env.PORT ?? '3000', 10) },
  supabase: { url: process.env.SUPABASE_URL, serviceKey: process.env.SUPABASE_SERVICE_KEY, databaseUrl: process.env.DATABASE_URL },
  redis: { host: process.env.REDIS_HOST ?? 'localhost', port: parseInt(process.env.REDIS_PORT ?? '6379', 10), password: process.env.REDIS_PASSWORD ?? '' },
  evolution: { apiUrl: process.env.EVOLUTION_API_URL, apiKey: process.env.EVOLUTION_API_KEY },
  anthropic: { apiKey: process.env.ANTHROPIC_API_KEY, model: process.env.ANTHROPIC_MODEL ?? 'claude-haiku-4-5' },
  ical: { syncIntervalMinutes: parseInt(process.env.ICAL_SYNC_INTERVAL_MINUTES ?? '15', 10) },
});
```

### BullMQ Queue Registration

`BullModule.forRootAsync()` in `AppModule` must use `ConfigService` to read Redis config:

```typescript
BullModule.forRootAsync({
  imports: [ConfigModule],
  useFactory: (config: ConfigService) => ({
    connection: {
      host: config.get('redis.host'),
      port: config.get<number>('redis.port'),
      password: config.get('redis.password') || undefined,
    },
  }),
  inject: [ConfigService],
})
```

Two named queues will be registered by their owning modules in later features: `ical-sync` (ChannelManagerModule) and `owner-alerts` (OwnerAlertsModule). Bootstrap does not register these queues — it only registers the BullMQ root connection.

### Swagger Setup

`main.ts` must configure Swagger as follows:
- `DocumentBuilder` with title `"PMS API"`, description `"WhatsApp-first Property Management System"`, version `"1.0"`
- `SwaggerModule.setup('docs', app, document)`
- Swagger must be set up before `app.listen()`

### Fastify + Versioning

- Adapter: `new FastifyAdapter({ logger: false })` — logger disabled in bootstrap (structured logging is M2 scope)
- URI versioning: `app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' })`
- CORS: `app.enableCors()` — allow all origins in v1 (auth + CORS hardening is M2 scope)

---

## Tasks

```
TASK-001: Project configuration files (package.json, tsconfig, nest-cli, .gitignore)
  Depends on: none
  Files:
    package.json
    tsconfig.json
    tsconfig.build.json
    nest-cli.json
    .gitignore
  Done when:
    - `npm install` exits 0
    - `npx tsc --version` prints TypeScript 5.x
    - `@shared/*`, `@modules/*`, `@config/*` path aliases are defined in tsconfig.json `paths`
    - tsconfig.build.json excludes `**/*.spec.ts` and `test/`
    - nest-cli.json has `"sourceRoot": "src"` and `"deleteOutDir": true`
    - .gitignore contains: node_modules/, dist/, .env, coverage/

TASK-002: Linting and formatting configuration (.eslintrc.js, .prettierrc)
  Depends on: TASK-001
  Files:
    .eslintrc.js
    .prettierrc
  Done when:
    - `npm run lint` exits 0 on an empty `src/` directory
    - .eslintrc.js has `@typescript-eslint/no-explicit-any: error`
    - .eslintrc.js has `@typescript-eslint/no-unused-vars: error`
    - .prettierrc has singleQuote: true, trailingComma: "all", printWidth: 100

TASK-003: Environment template (.env.example)
  Depends on: none
  Files:
    .env.example
  Done when:
    - All 12 env vars from the Config Groups table are present
    - Each var has an inline comment explaining its purpose
    - Required vars have no default value assigned (e.g., `SUPABASE_URL=`)
    - Optional vars show their default (e.g., `PORT=3000`)

TASK-004: Configuration factory (src/config/configuration.ts)
  Depends on: TASK-001
  Files:
    src/config/configuration.ts
  Done when:
    - Default export is a function returning the typed config object
    - All 12 env vars are mapped to their config paths as specified in the Config Groups table
    - Numeric conversions use `parseInt(..., 10)`
    - No env var is read directly outside this file (single source of truth)

TASK-005: SupabaseService and DatabaseModule
  Depends on: TASK-001, TASK-004
  Files:
    src/shared/database/supabase.service.ts
    src/shared/database/database.module.ts
  Done when:
    - `SupabaseService` implements `OnModuleInit`
    - `onModuleInit()` calls `createClient(url, serviceKey)` and stores the result
    - `get db()` returns the stored `SupabaseClient` instance
    - `DatabaseModule` is decorated with `@Global()` and `@Module({ providers: [SupabaseService], exports: [SupabaseService] })`
    - `DatabaseModule` does NOT import `ConfigModule` directly — it uses the globally available `ConfigService`

TASK-006: Domain module stubs (all 8 modules)
  Depends on: TASK-001
  Files:
    src/modules/properties/properties.module.ts
    src/modules/reservations/reservations.module.ts
    src/modules/guests/guests.module.ts
    src/modules/channel-manager/channel-manager.module.ts
    src/modules/owner-alerts/owner-alerts.module.ts
    src/modules/messaging/messaging.module.ts
    src/modules/financials/financials.module.ts
    src/modules/cleaning/cleaning.module.ts
  Done when:
    - Each file exports a class decorated with `@Module({ imports: [], controllers: [], providers: [] })`
    - Class names follow the pattern: `PropertiesModule`, `ReservationsModule`, etc.
    - No service, controller, or provider is defined — stubs only

TASK-007: AppModule root wiring (src/app.module.ts)
  Depends on: TASK-004, TASK-005, TASK-006
  Files:
    src/app.module.ts
  Done when:
    - `ConfigModule.forRoot({ isGlobal: true, load: [configuration] })` is imported
    - `EventEmitterModule.forRoot()` is imported
    - `ScheduleModule.forRoot()` is imported
    - `BullModule.forRootAsync(...)` is imported with Redis config read from `ConfigService` as specified in Design
    - `DatabaseModule` is imported
    - All 8 domain module stubs are imported
    - `AppModule` itself has no controllers or providers

TASK-008: Application entry point (src/main.ts)
  Depends on: TASK-007
  Files:
    src/main.ts
  Done when:
    - `NestFactory.create` uses `FastifyAdapter` with `logger: false`
    - `ValidationPipe` is applied globally with `whitelist: true`, `forbidNonWhitelisted: true`, `transform: true`
    - `app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' })` is called
    - `app.enableCors()` is called
    - Swagger `DocumentBuilder` sets title, description, version; `SwaggerModule.setup('docs', app, document)` is called
    - `app.listen(port, '0.0.0.0')` uses `config.get<number>('app.port')` — `ConfigService` is obtained via `app.get(ConfigService)`
    - `npm run start:dev` starts without error and `GET /docs` returns 200

TASK-009: Database migration (supabase/migrations/001_initial_schema.sql)
  Depends on: none
  Files:
    supabase/migrations/001_initial_schema.sql
  Done when:
    - All 9 CREATE TABLE statements are present in the correct dependency order: tenants, properties, ota_connections, guests, reservations, calendar_blocks, cleaning_tasks, financial_records, message_logs
    - Every FK references an existing table
    - All CHECK constraints for enum-like columns are present (platform, status, checkin_status, type, direction, channel)
    - All UNIQUE constraints are present (tenants.whatsapp_number, guests(tenant_id,phone), reservations(property_id,platform,external_id), ota_connections(property_id,platform))
    - All indexes from the DB Schema section are present
    - Running the file against a blank PostgreSQL instance (via `psql` or Supabase SQL editor) completes with no errors
```

---

## Out of Scope

- **Authentication / JWT guards** — deferred to M2. TEMP_TENANT_ID placeholder is sufficient for M1.
- **Row-level security (RLS) policies** — deferred to M2 alongside auth.
- **Supabase Storage bucket configuration** — needed for document photos in Check-in Digital (M2).
- **Bull Board dashboard** — observability tooling is M2 scope.
- **Structured logging (Pino)** — M2 scope; `logger: false` in Fastify adapter for now.
- **Health check endpoint** (`/health`) — M2 scope.
- **Jest configuration customisation** — default `nest new` jest config is sufficient; advanced test setup is per-module.
- **Docker / docker-compose** — infrastructure provisioning is out of spec scope; developers run Redis and point to Supabase directly.
- **Domain module implementations** — each module stub will be fleshed out in its own feature spec (Properties, Channel Manager, etc.).
- **CI/CD pipeline** — not part of M1 bootstrap.
- **`.env` validation on startup (e.g., Joi schema)** — deferred; `configuration.ts` returns `undefined` for missing vars and each service is responsible for failing fast when it tries to use them.
