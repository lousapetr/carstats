# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Do NOT add comments to fixed code explaining why the 
original code was incorrect. Only ever comment on active things
that are hard to get from context.

The repo root carries untracked dotfiles that are not part of CarStats (`.bashrc`,
`.zshrc`, `.gitconfig`, `.idea`, `.mcp.json`, several `.claude/` subdirectories). They are
environment leftovers — never stage them; stage only the files you actually changed, and
don't bother reporting them as pending work.

Commit directly to main branch.

## Project overview

CarStats is a personal single-user car logging app: fuel fill-ups, maintenance/service
history (with invoice/photo attachments), due-date/due-mileage reminders, and a cost
dashboard shown in CZK regardless of what currency entries were logged in. Backend is
FastAPI + SQLModel + SQLite; frontend is React + Vite + TypeScript + Tailwind. The whole
UI is in Czech (no i18n framework — strings are just written in Czech directly). Access is
gated behind Google OAuth restricted to an allowlist of emails
(`CARSTATS_ALLOWED_EMAILS`), all sharing the one dataset.

## Commands

### Backend (`backend/`)

```bash
uv sync                          # install deps
cp .env.example .env             # CARSTATS_SESSION_SECRET + CARSTATS_ALLOWED_EMAILS required
uv run alembic upgrade head      # apply migrations (required before first run)
uv run uvicorn app.main:app --reload   # serve on :8000, docs at /docs

uv run pytest                    # full backend test suite
uv run pytest tests/test_fuel.py                    # one file
uv run pytest tests/test_fuel.py::test_create_fuel_entry_updates_car_mileage  # one test
uv run pytest -k mileage         # by keyword

uv run ruff check .              # lint
uv run basedpyright              # type check (app/ only; tests + generated migrations ignored)
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

Because mileage is validated to rise with date, it is also the **ordering key** for fuel and
service entries everywhere — lists, exports, charts and the dashboard activity log sort by
`mileage_km` (then `id`), never by `date`: two fill-ups on one day are common, and a date sort
leaves them in arbitrary order.

`CarProfile` itself is a lazily-created singleton row (`get_or_create_profile`), not a
multi-vehicle table.

### Currency: snapshot-at-entry-time, not live conversion

`CurrencyRate` holds one `rate_to_czk` per non-CZK currency (CZK is always 1.0, not
stored), lazily seeded from `DEFAULT_RATES_TO_CZK` and then refreshed from the ČNB daily
fixing at most once per calendar day (`_ensure_rates_fresh`); a failed or unparseable fetch
logs a warning and keeps the cached rates, then backs off for `FETCH_RETRY_AFTER` rather than
pinning the whole day. That once-a-day check reads the newest row's `updated_at`, so seeded
rows are stamped `SEEDED_AT` (1970) instead of "now" — `updated_at` means "when ČNB last told
us this rate", and a seeded-only table must not look fresh. `parse_rates` skips a row it cannot
make sense of instead of discarding the whole fixing, and `_ensure_rates_fresh` catches broadly
on top of that, because it runs inside entry creation and must never 500 it. Rates are
read-only to the user — there is no
`PUT`, and the fuel/maintenance forms show the current rate disabled, for information only.

Every `FuelEntry`/`ServiceEntry` stores the *original* currency/amount plus a copy of the
exchange rate that was active when it was logged (`exchange_rate` column), so a later
fixing never retroactively changes past dashboard totals — the dashboard
(`dashboard/service.py`) always sums the CZK-converted values using each entry's own stored
rate, never today's. When adding new money fields, follow this pattern rather than
converting on read.

### Dashboard: one period-scoped endpoint

`GET /api/dashboard?period=…` is the dashboard's only endpoint and returns everything the page
shows, so one `date.today()` scopes it all and one selector change is one refetch. `period` is
`all | ytd | 12m | year:YYYY | range:YYYY-MM-DD..YYYY-MM-DD` (default `all`, `PERIOD_PATTERN` in
`dashboard/periods.py`; anything else — including a nonexistent date or a reversed range — is a
422). `12m` is the current month plus the eleven before it; `ytd` is compared with the *same
stretch* of last year (29 Feb falls back to the 28th), not the whole year; a custom `range` is
compared with the same number of days just before it. `all` has no previous window, so no
deltas.

Two filtering rules live side by side in `get_dashboard`, on purpose: **costs filter entries** by
date, but **consumption filters intervals** — `full_to_full_intervals()` runs over the whole fuel
history, then intervals are kept by the date of the full tank that closes them. Filtering entries
first would drop an interval straddling the window start and understate the first one (a partial
fill just before the boundary goes missing). An interval therefore belongs wholly to the period it
closed in, which is also where its figure shows in the fuel log. Don't touch `fuel/service.py` to
change this; call it differently. `distance_km` starts from the newest reading *before* the window.

`car` (the odometer) and `upcoming_reminders` are deliberately *not* period-scoped; the page puts
them above the selector to say so. The selected period lives only in the URL (`?period=`), and the
query key is `['dashboard', period]`, so the log pages' `invalidateQueries(['dashboard'])` still
covers every period. Labels ("Letos", "vs. 2025") are composed on the frontend
(`lib/periods.ts`); the API returns keys and dates, never Czech text.

### Auth

Server-side session cookie only (Starlette `SessionMiddleware`, no JWT/localStorage).
`/auth/login` → Google OAuth → `/auth/callback` rejects an email Google reports as
unverified, then checks it against the `ALLOWED_EMAILS` allowlist before setting the
session. Every failure in the callback — a token exchange that raises (a refreshed or
bookmarked callback URL reuses a single-use code, a stale `state`, a cancelled consent
screen) as well as the three post-exchange rejections — redirects to `/?error=<code>`
instead of raising, because the caller is a browser following a redirect and a raw JSON
403 (or a 500) leaves it with no way back. `LoginScreen.tsx` maps the code to a Czech
message and strips the parameter; a new failure path needs an entry in both. The `CurrentUser` dependency (`core/security.py`) gates every `/api/*` route
(and `/auth/me`), and it re-checks the allowlist on *every* request, not only at login —
with no server-side session store, a login-time-only check would leave a dropped address
working until its cookie expired, and rotating `CARSTATS_SESSION_SECRET` (which signs
everyone out) would be the only way to revoke one person. Keep that re-check; it is why
the 30-day `SESSION_MAX_AGE_SECONDS` is safe to keep as long as it is.

`CARSTATS_ALLOWED_EMAILS` is a comma-separated string, not a `list[str]` field:
pydantic-settings JSON-decodes complex-typed fields from the environment and would crash
at import on `a@x.com,b@y.com`. `Settings.allowed_email_set` does the splitting, stripping
and lowercasing, so `is_email_allowed()` is a plain membership test that fails closed —
an unset or separators-only value parses to an empty set. Everyone on the list shares the
one car and dataset; there is no per-user data partitioning.

`Settings` refuses to construct unless `CARSTATS_SESSION_SECRET` is at least
`MIN_SESSION_SECRET_LENGTH` characters (`core/config.py`), so a missing or placeholder
secret crashes the app at import instead of letting anyone forge a signed session cookie.
Because every app import constructs `Settings`, `tests/conftest.py` sets a secret in
`os.environ` *above* its `from app…` imports — keep that ordering.

The cookie is `same_site="lax"`, `httponly`, capped at `SESSION_MAX_AGE_SECONDS` (30 days)
and `Secure` per `settings.session_cookie_secure`. That flag has no fixed default: it
follows the scheme of `CARSTATS_OAUTH_REDIRECT_URL` (https in production behind the tunnel,
http for local dev where a Secure cookie would never come back), and
`CARSTATS_COOKIE_SECURE` overrides it explicitly. `same_site="lax"` is the only CSRF
defence in the app — there is no CSRF token — so don't loosen it to `none`.

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
for every failed mutation. A new form's validation errors get this for free — no
per-mutation `onError` needed. `api/errors.ts::mutationErrorMessage` picks the text: a
Czech message for 401/404/413, otherwise the backend's `detail` verbatim, and a generic
Czech line only when the response carried no `detail` at all — a specific English message
is preferred over a generic Czech one. Backend 400 `detail`s are user-facing and must be
written in Czech (see `car/service.py`, `attachments/storage.py`); a 422's `detail` is a
list of pydantic errors, which `api/client.ts` flattens into one message.

Failed *reads* don't toast: each page renders `components/ui/LoadingState` /
`ErrorState` (with a retry button calling `refetch`) off the query's `isPending` /
`isError` — use `isPending`, not `isLoading`, or a failed query shows "Načítám…" forever.
Queries retry once, only on a network error or 5xx. A 401 from any query or mutation
clears the cached `['auth', 'me']`, which drops the user back on the login screen.

The forms hand `onSubmit` the mutation *promise* (`mutateAsync`) and clear themselves only
once it resolves, so a rejected entry stays on screen to be corrected — don't go back to
`mutate` + an unconditional `reset()`.

### Tests

`backend/tests/conftest.py` gives each test a fresh temp-file SQLite DB via the `client`
(authenticated) and `anon_client` (unauthenticated, for 401 checks) fixtures — tests never
touch the real dev `data/carstats.db`.

SQLite FK enforcement is per-engine, via `enable_sqlite_foreign_keys()` in
`core/database.py`; any new engine (including a test fixture's) must call it, or
`ON DELETE CASCADE` silently does nothing. Alembic's engine deliberately does not.

## Deployment

Single Docker image (multi-stage: Node build → Python runtime) serving both the API and
the built frontend from one process, deployed via `docker-compose.yml` (app + `cloudflared`)
to an Oracle Cloud "Always Free" VM, tunneled through Cloudflare for HTTPS with no open
ports. `deploy.sh` on the VM does `git pull && docker compose up -d --build`. SQLite DB and
uploaded attachments live in the `carstats_data` Docker volume, surviving redeploys. The
image sets `TZ=Europe/Prague` (with `tzdata` installed), so `date.today()` — which drives
reminder due dates and the dashboard's relative periods — turns over at Czech midnight;
stored timestamps are all explicit `datetime.now(UTC)` and unaffected. Full
one-time setup steps (Google OAuth client, Cloudflare Tunnel, secrets) are in `README.md`.
