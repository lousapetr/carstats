# TODO

Open work lives in [GitHub issues](https://github.com/lousapetr/carstats/issues). This file is
the index: what a review found, where it went, and what was deliberately left alone.

---

## Code review — 2026-09-28 (`a066864`)

Full-codebase pass over architecture, structure, security and maintainability, plus a dashboard
evaluation. Measured against a green tree: 83 tests passing, `ruff check` clean.

The core designs came out well and should not be disturbed — domain-per-directory on the backend,
the snapshot-at-write-time currency model, the shared mileage helpers in `car/service.py`, and the
single-artifact FastAPI-serves-the-SPA deploy. The weaknesses are at the edges.

### Fix first

| # | Issue | Why it matters |
|---|-------|----------------|
| [#2](https://github.com/lousapetr/carstats/issues/2) | `.env.example`'s placeholder session secret passes the 32-char guard | It is exactly 33 chars, so the guard lets a **world-readable signing key** into production — the repo is public. Check the VM's `.env` before anything else. |
| [#3](https://github.com/lousapetr/carstats/issues/3) | Allowlist removal doesn't revoke the session | `is_email_allowed` is checked only at login, so a removed address keeps access for up to 30 days. |

### Correctness and data integrity

| # | Issue | Why it matters |
|---|-------|----------------|
| [#4](https://github.com/lousapetr/carstats/issues/4) | Deleting a service entry orphans its attachments, and SQLite id reuse re-attaches them | A new entry silently shows a deleted entry's invoices. No cascade, `PRAGMA foreign_keys` is off. |
| [#5](https://github.com/lousapetr/carstats/issues/5) | No numeric or length validation on fuel, service, reminder input | `recurrence_days=-30` pins a reminder to `overdue` forever. Zero-litre fill-ups accepted. |
| [#6](https://github.com/lousapetr/carstats/issues/6) | A failed ČNB fetch stamps seeded defaults as fresh and never retries that day | Approximate 2025 rates get **permanently** snapshotted into a whole day of foreign-currency entries. |
| [#7](https://github.com/lousapetr/carstats/issues/7) | `ZeroDivisionError` escapes the ČNB parser | An upstream data glitch 500s entry creation, which is the app's main job. |
| [#8](https://github.com/lousapetr/carstats/issues/8) | Uncaught `OAuthError` in `/auth/callback` → 500 | A refreshed callback URL or a cancelled consent screen gives an opaque error with no way back. |
| [#9](https://github.com/lousapetr/carstats/issues/9) | Service worker hijacks CSV exports and attachment downloads | `navigateFallbackDenylist` is one prefix short, so downloads return `index.html`. Live, user-visible, invisible in `npm run dev`. |
| [#10](https://github.com/lousapetr/carstats/issues/10) | Two migration downgrades silently corrupt data | Dropping `full_tank` makes every consumption figure plausibly wrong; dropping `exchange_rate` turns 40 EUR into 40 Kč. Also `render_as_batch` is missing from `env.py`. |

### Dashboard

Evaluated in full; the work splits into four issues. The first three are frontend-only and
independent, so they land value before any API change.

| # | Issue |
|---|-------|
| [#11](https://github.com/lousapetr/carstats/issues/11) | Loading, error and empty states — `isError` appears **zero times** in `src/`, so a failed query shows "Načítám…" forever |
| [#12](https://github.com/lousapetr/carstats/issues/12) | Drop the dual-axis price chart; fix readability, contrast and accessible names |
| [#13](https://github.com/lousapetr/carstats/issues/13) | Centralise number formatting and the Czech service-type labels (4 duplicates) |
| [#14](https://github.com/lousapetr/carstats/issues/14) | Period filtering, hierarchy (9 flat tiles → hero + 4), and a monthly cost chart |

### Backlogs

| # | Issue |
|---|-------|
| [#15](https://github.com/lousapetr/carstats/issues/15) | Maintainability backlog — 13 items, checkboxed. **No CI** leads it and is the highest-leverage gap in the repo. |
| [#16](https://github.com/lousapetr/carstats/issues/16) | Feature backlog — 8 ideas. Consumption anomaly flagging is the best value-per-line. |

### Deliberately not done

Recorded so they aren't rediscovered as oversights.

**Rate limiting** — completely absent, and defensible for a two-user app behind a Cloudflare
Tunnel. An **accepted risk**, not a gap.

**CORS** — correctly absent. Same-origin by construction; FastAPI serves the built SPA and the
client uses `credentials: 'same-origin'`. Adding `CORSMiddleware` with `allow_credentials=True`
would be the mistake.

**Per-user data partitioning** — everyone on the allowlist deliberately shares one car and one
dataset. Any allowlisted address can read every invoice; that is the intended design.

**Vitest** — the 2026-09-09 decision below still stands. The compensating move is putting new
arithmetic on the backend, where the tests already are: that's why #14 computes period windows and
deltas server-side rather than in the browser.

**Rewriting `validate_mileage_consistency`** — declined in the 2026-09-09 review (finding 10) with
sound reasoning; nothing has changed.

**Dashboard full-table scans** — three endpoints each scan `fuelentry` and `serviceentry`.
Collapsing to one endpoint (#14) removes two of the three for free, and the remaining `FuelEntry`
scan is *required*: full-to-full accounting needs every row regardless of the selected period.
Pushing sums into SQL would leave that scan in place, add round-trips, and duplicate the CZK
conversion formula. **Revisit at** ~10 000 fuel rows or `/api/dashboard` p95 over 200 ms; the first
move then is memoizing `full_to_full_intervals` on (row count, max id), not SQL aggregates.

**Consumption-by-season chart** — cheap and genuinely interesting, but 1–3 years of data gives 1–4
intervals per month, so the chart is noise. **Revisit at** ≥2 full calendar years of full-tank
intervals.

**Fuel price vs the national average** — rejected outright. ČNB publishes FX, not fuel prices, so
it needs a new ČSÚ/CCS scraper, table and daily failure mode for a comparison that changes no
decision the driver can act on.

---

## Code review — 2026-09-09 (`5a76116`), closed out 2026-09-27

The full-codebase review's 17 findings have all been addressed. What shipped, in the
order it was fixed (see `git log` for the commits):

| # | Finding | Outcome |
|---|---------|---------|
| 1 | Session secret fell back to a hardcoded default | fixed 2026-09-22 — `Settings` refuses to construct below `MIN_SESSION_SECRET_LENGTH` |
| 2 | Session cookie missing `Secure` / `max_age` | fixed 2026-09-22 — `https_only` follows the redirect URL's scheme, 30-day `max_age` |
| 4 | Average consumption was an unweighted mean | fixed 2026-09-27 — `full_to_full_intervals()`, distance-weighted, split by year |
| 11 | `get_summary` re-queried fuel entries | fixed 2026-09-27 with finding 4 |
| 3 + 12 | Completing a recurrence with no due field was a no-op | fixed — rolls forward from today / current mileage; `timedelta` arithmetic |
| 8 | Backend 422s showed the user nothing | fixed — `client.ts` flattens the pydantic error list, toast fires on 422 too |
| 7 | Failed submissions wiped the form | fixed — forms await `mutateAsync` and reset only on success |
| 5 | Attachment upload unbounded and untyped | fixed — 20 MB streamed cap, PDF/image allowlist, partial file removed |
| 6 | ČNB fetch failures swallowed, no logging | fixed — narrowed catch, `logger.warning` with traceback, also warns on an empty parse |
| 15 | Unknown `/api/*` returned `index.html` with a 200 | fixed — the catch-all 404s `api/` and `auth/` prefixes |
| 17 | `CarProfileUpdate` accepted any year | fixed — `ge=1900, le=2100` |
| 14 | `confirmDialog` hung with no listener | fixed — resolves `false`; attachment delete now confirms too |
| 13 | `useIsDark` was a snapshot, duplicated | fixed — one real hook in `lib/useIsDark.ts`, subscribed to the media query |
| 9 | N+1 attachment queries, unindexed FK | fixed — one grouped query, `ix_attachment_service_entry_id` |
| 16 | Docs described editable exchange rates | fixed — `CLAUDE.md` now describes the ČNB-only, read-only rates |

### Deliberately not done

**10 — rewriting `validate_mileage_consistency` into per-side `MAX`/`MIN` queries.**
The `date` indexes it asked for did land (with finding 9's migration), but the query
rewrite did not: it trades two readable `SELECT`s that the exclude-id logic filters in
Python for four aggregate queries with the same logic pushed into `WHERE` clauses, to save
milliseconds on a few hundred rows. `_consumption_for_entry` re-reading all fuel entries is
inherent to full-to-full accounting, which needs the whole history anyway. Revisit if the
log ever reaches tens of thousands of rows.

### Known gap

No frontend test runner is configured, so the client-side fixes above (findings 7, 8, 13,
14) are verified by `tsc`/`vite build` and manual testing only. Standing up Vitest for an
app this size hasn't been worth it yet.
