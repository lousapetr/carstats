# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

CarStats is a personal single-user car logging app: fuel fill-ups, maintenance/service
history (with invoice/photo attachments), due-date/due-mileage reminders, and a cost
dashboard shown in CZK regardless of what currency entries were logged in. Backend is
FastAPI + SQLModel + SQLite; frontend is React + Vite + TypeScript + Tailwind. The whole
UI is in Czech (no i18n framework — strings are just written in Czech directly). Access is
gated behind Google OAuth restricted to a single allowed email (`CARSTATS_ALLOWED_EMAIL`).

## Commands

### Backend (`backend/`)

```bash
uv sync                          # install deps
cp .env.example .env             # fill in CARSTATS_ALLOWED_EMAIL at minimum
uv run alembic upgrade head      # apply migrations (required before first run)
uv run uvicorn app.main:app --reload   # serve on :8000, docs at /docs

uv run pytest                    # full backend test suite
uv run pytest tests/test_fuel.py                    # one file
uv run pytest tests/test_fuel.py::test_create_fuel_entry_updates_car_mileage  # one test
uv run pytest -k mileage         # by keyword

uv run ruff check .              # lint
uv run alembic revision --autogenerate -m "message"  # new migration
```

Real Google sign-in requires registered OAuth credentials and a reachable redirect URL;
without them `/api/*` returns 401 locally, which is expected — most backend work can be
verified via `pytest` or FastAPI's `TestClient` without a real login.

### Frontend (`frontend/`)

```bash
npm install
npm run dev      # :5173, proxies /api and /auth to :8000 (see vite.config.ts)
npm run build    # tsc -b && vite build; also generates the PWA manifest/service worker
npm run lint     # oxlint
```

No frontend test runner is configured — verification is via `tsc`/`vite build` (type
errors fail the build) and manual testing.

## Architecture

### Backend: modular by domain, not by layer

`backend/app/` has one directory per domain (`car`, `fuel`, `maintenance`, `reminders`,
`currency`, `attachments`, `export`, `dashboard`, `auth`), each with its own
`models.py`/`schemas.py`/`service.py`/`router.py` — not a flat `models.py`/`routes.py`
split. `dashboard` and `export` have no models of their own; they read across the other
domains' tables. All models must be imported in both `alembic/env.py` and
`tests/conftest.py` so `SQLModel.metadata` is fully populated for migrations/tests — a new
domain module needs adding to both.

### Cross-cutting logic lives in `car/service.py`

Even though it's named for the `car` domain, `car/service.py` holds two helpers shared by
`fuel` and `maintenance`:
- `recalculate_current_mileage()` — recomputes `CarProfile.current_mileage_km` as the max
  across all fuel + service entries. Called after every create/update/delete in both
  domains so edits/deletes of the highest-mileage entry don't leave stale data (a plain
  "bump if higher" would).
- `validate_mileage_consistency()` — a new/edited entry's mileage must sit between its
  date-neighbors across *both* fuel and service history (not just its own table), raising
  `ValueError` (→ HTTP 400) otherwise. This allows historical backfill out of chronological
  upload order while still catching typos.

`CarProfile` itself is a lazily-created singleton row (`get_or_create_profile`), not a
multi-vehicle table.

### Currency: snapshot-at-entry-time, not live conversion

`CurrencyRate` holds one editable `rate_to_czk` per non-CZK currency (CZK is always 1.0,
not stored), lazily seeded with starter defaults from `DEFAULT_RATES_TO_CZK` on first
access. Every `FuelEntry`/`ServiceEntry` stores the *original* currency/amount plus a copy
of the exchange rate that was active when it was logged (`exchange_rate` column). This
means editing a rate in Settings never retroactively changes past dashboard totals — the
dashboard (`dashboard/service.py`) always sums the CZK-converted values using each entry's
own stored rate, never today's rate. When adding new money fields, follow this pattern
rather than converting on read.

### Auth

Server-side session cookie only (Starlette `SessionMiddleware`, no JWT/localStorage).
`/auth/login` → Google OAuth → `/auth/callback` checks the returned email against
`ALLOWED_EMAIL` (case-insensitive, fails closed if unset) and sets the session. The
`CurrentUser` dependency (`core/security.py`) gates every `/api/*` route.

### Single deploy artifact: FastAPI serves the built SPA

`main.py`'s catch-all route serves real files from the Vite build (`favicon.svg`,
`manifest.webmanifest`, service worker files — anything at the dist root, not just
`/assets/*`) when they exist on disk, falling back to `index.html` for genuine client-side
routes. This check resolves the path and verifies it's still inside `frontend_dist_dir`
before serving, to prevent directory traversal via a crafted URL — don't simplify this back
to an unconditional `FileResponse(index.html)` or unguarded path join.

### Frontend: feature folders + one global error channel

`src/features/<domain>/` co-locates a domain's page + form + hooks. Shared primitives live
in `src/components/ui/`. Server state is TanStack Query; forms are react-hook-form + zod
(note the `useForm<Input, unknown, Output>` three-generic pattern in forms using
`z.coerce`/`z.preprocess` — needed because the resolver's input/output types diverge, see
`FuelForm.tsx`).

Error popups are not wired per-form: `App.tsx` configures the shared `QueryClient` with a
`MutationCache.onError` that shows a toast (`lib/toastBus.ts` + `components/ui/ToastHost.tsx`)
for any mutation failing with HTTP 400. A new form's validation errors get this for free —
no per-mutation `onError` needed. Backend 400 `detail` messages are shown verbatim, so they
must be written in Czech (see `car/service.py`, `currency/service.py`).

### Tests

`backend/tests/conftest.py` gives each test a fresh temp-file SQLite DB via the `client`
(authenticated) and `anon_client` (unauthenticated, for 401 checks) fixtures — tests never
touch the real dev `data/carstats.db`.

## Deployment

Single Docker image (multi-stage: Node build → Python runtime) serving both the API and
the built frontend from one process, deployed via `docker-compose.yml` (app + `cloudflared`)
to an Oracle Cloud "Always Free" VM, tunneled through Cloudflare for HTTPS with no open
ports. `deploy.sh` on the VM does `git pull && docker compose up -d --build`. SQLite DB and
uploaded attachments live in the `carstats_data` Docker volume, surviving redeploys. Full
one-time setup steps (Google OAuth client, Cloudflare Tunnel, secrets) are in `README.md`.
