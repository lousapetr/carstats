# TODO

All five items from the previous session's plan have shipped:

1. Maskable PWA home-screen icon — `aba0cec`
2. "Aditiva" maintenance type — `3783998`
3. Full-to-full consumption accounting for partial fill-ups — `0f6d147`
4. Price-per-liter on the fuel trend chart — `2910689`
5. Inline, editable exchange rate on fuel/maintenance forms — `9f4f59f`

Nothing queued right now — add new items here as they come up.

---

## Code review — 2026-09-09 13:39 CEST (`5a76116`)

Full-codebase review (backend `app/` + `tests/`, frontend `src/`, Docker/deploy), run
against the project's code-review checklist: security → error handling → performance →
code quality → testing. Baseline at review time: `ruff check` clean, 52/52 backend tests
passing. Findings are ordered by severity.

### CRITICAL

**1. Session secret silently falls back to a hardcoded default → full auth bypass**
`backend/app/core/config.py:9`, used at `backend/app/main.py:21`

If `CARSTATS_SESSION_SECRET` is missing from the environment, `Settings` quietly uses
`"dev-secret-change-me"` and the app boots normally. Anyone who knows that value (it is in
this public repo) can mint a valid `itsdangerous`-signed session cookie containing
`{"user_email": "<allowed email>"}` and skip Google OAuth and the `ALLOWED_EMAIL`
allowlist entirely. `docker/entrypoint.sh` does not check for it either, so a deploy that
drops the var from `.env` degrades to wide-open with no visible symptom. Note the
allowlist itself already fails closed (`auth/service.py:6`) — the session secret should
too.

Fix — make the app refuse to start without a real secret:

```python
# backend/app/core/config.py
from pydantic import model_validator

class Settings(BaseSettings):
    session_secret: str = ""
    ...

    @model_validator(mode="after")
    def _require_session_secret(self) -> "Settings":
        if not self.session_secret or self.session_secret.startswith("change-me"):
            raise ValueError(
                "CARSTATS_SESSION_SECRET must be set to a random value "
                "(generate: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
            )
        return self
```

Then drop the `session_secret` default from `.env.example`'s placeholder wording so the
copy-paste `.env` fails loudly rather than running insecurely.

---

### WARNING

**2. Session cookie is missing the `Secure` flag**
`backend/app/main.py:21`

`SessionMiddleware(..., same_site="lax")` sets no `https_only`, so the cookie is sent over
plain HTTP too. The deployment is HTTPS-only via the Cloudflare tunnel, so this is
hardening rather than an active hole — but `same_site="lax"` is currently the *only* thing
standing between this app and CSRF on every `POST`/`PUT`/`DELETE` (there is no CSRF token
anywhere), which makes the cookie's transport flags worth getting right. Also consider a
`max_age` so an abandoned session eventually expires.

```python
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.cookie_secure,   # new setting, default True; False for local dev
    max_age=60 * 60 * 24 * 30,
)
```

**3. Completing a reminder that recurs but has no matching due field is a permanent no-op**
`backend/app/reminders/service.py:86-103`

`complete_reminder` only rolls the due date forward when *both* `recurrence_days` and
`due_date` are set (same for `recurrence_km`/`due_mileage_km`), but `is_recurring` is
computed from the recurrence fields alone. A reminder with `recurrence_days=180` and no
`due_date` therefore takes the `completed_at = None` branch without advancing anything:
"Hotovo" returns 200, nothing changes, and the reminder is stuck in the active list
forever with no way out but deletion. The UI permits exactly this — `ReminderForm.tsx`
marks every date/mileage field optional.

Verified against the running app:

```
POST /api/reminders {"title": "Olej", "recurrence_days": 180}
POST /api/reminders/1/complete  -> 200 {"due_date": null, "completed_at": null, ...}
GET  /api/reminders             -> still lists "Olej", unchanged
```

Fix — treat a recurrence as active only when it has something to advance:

```python
def complete_reminder(db: Session, reminder: Reminder) -> ReminderRead:
    rolled = False
    if reminder.recurrence_days is not None:
        base = max(reminder.due_date, date.today()) if reminder.due_date else date.today()
        reminder.due_date = base + timedelta(days=reminder.recurrence_days)
        rolled = True
    if reminder.recurrence_km is not None:
        profile = get_or_create_profile(db)
        base_mileage = max(reminder.due_mileage_km or 0, profile.current_mileage_km)
        reminder.due_mileage_km = base_mileage + reminder.recurrence_km
        rolled = True

    reminder.completed_at = None if rolled else datetime.now(UTC)
    ...
```

(This also replaces `base.fromordinal(base.toordinal() + n)` with `base + timedelta(days=n)` —
see finding 12.)

**4. Average consumption is an unweighted mean of intervals, not litres per distance**
`backend/app/dashboard/service.py:64-69`

`avg_consumption_l_per_100km` averages the per-interval `consumption_l_per_100km` values
with equal weight, so a 100 km top-up counts as much as a 1000 km tank. The headline
dashboard number can be off by 2× on realistic data.

Verified against the running app — 1000 km at 5 l/100 km followed by 100 km at
20 l/100 km:

```
per-entry consumptions: [5.0, 20.0]
avg reported: 12.5 l/100 km      true (70 l / 1100 km): 6.36 l/100 km
```

Fix — weight by distance, i.e. total litres over total distance across full-to-full
intervals. `_compute_consumptions` already walks exactly those intervals; have it also
return the litres and distance per interval (or add a sibling helper) and compute:

```python
total_l, total_km = fuel_service.full_to_full_totals(db)
avg_consumption = round(total_l / total_km * 100, 2) if total_km > 0 else None
```

**5. Attachment upload has no size limit and no server-side type check**
`backend/app/attachments/storage.py:20`, `backend/app/attachments/router.py:20-37`

`upload.file.read()` pulls the entire upload into memory in one call, and nothing bounds
it — a large file OOMs the container (which has no memory limit in `docker-compose.yml`)
and fills the `carstats_data` volume that also holds the SQLite DB. The
`accept="image/*,application/pdf"` on `AttachmentUploader.tsx:62` is a file-picker hint
only; the API accepts any type. Auth limits this to one account, so it is a robustness
problem rather than an open door — but a mis-picked 4 GB file is a realistic accident.

```python
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic"}

def save_file(service_entry_id: int, upload: UploadFile) -> tuple[str, str, str]:
    content_type = upload.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Nepodporovaný typ souboru: {content_type}")
    ...
    written = 0
    with dest.open("wb") as fh:
        while chunk := upload.file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                fh.close(); dest.unlink(missing_ok=True)
                raise ValueError("Soubor je příliš velký (max 20 MB)")
            fh.write(chunk)
```

Raise `ValueError` and let the router map it to a 400, matching the existing fuel/service
convention so the frontend's `MutationCache.onError` toast picks it up for free.

**6. ČNB fetch failures are swallowed with a bare `except`, and there is no logging anywhere**
`backend/app/currency/service.py:38-41`

```python
try:
    rates = cnb_client.parse_rates(cnb_client.fetch_daily_text())
except Exception:
    return  # keep whatever we have
```

The fallback behaviour is right, but `except Exception: return` catches everything —
network errors, a ČNB format change that breaks `parse_rates`, a bug in the loop — and
leaves no trace. Because entries snapshot the rate at write time, a silently stale rate is
permanently baked into every entry logged that day. `grep -rn "logging" backend/app/`
returns nothing: the application has no logging at all, so this is invisible in
`docker compose logs`.

```python
import logging
logger = logging.getLogger(__name__)
...
except (httpx.HTTPError, ValueError, KeyError):
    logger.warning("ČNB rate fetch failed; keeping cached rates", exc_info=True)
    return
```

**7. Failed submissions wipe the user's form input**
`frontend/src/features/fuel/FuelForm.tsx:57-62`, `frontend/src/features/maintenance/MaintenanceForm.tsx:65-74`

```tsx
onSubmit={handleSubmit((values) => {
  onSubmit(values)          // fires the mutation, does not await it
  if (!defaultValues) {
    reset({ date: ..., currency: 'CZK', full_tank: true })   // runs immediately
  }
})}
```

`onSubmit` dispatches `createMutation.mutate(...)` and returns synchronously, so `reset()`
clears the form before the request resolves. When the backend rejects the entry — the
mileage-consistency 400 from `car/service.py:61-69`, which is a routine typo guard — the
user gets a toast explaining the problem and an empty form to retype from scratch. Reset
on success only:

```tsx
// in the page component
const createMutation = useMutation({
  mutationFn: fuelApi.create,
  onSuccess: () => { invalidate(); formRef.current?.resetToBlank() },
})
```

or, keeping the reset inside the form, pass a `resetSignal` prop the page bumps in
`onSuccess` and reset from a `useEffect` on it.

**8. Backend 422 responses show the user nothing**
`frontend/src/api/client.ts:22-23`, `frontend/src/App.tsx:19-21`

Two gaps compound. `MutationCache.onError` toasts only `status === 400`, and FastAPI
returns **422** for schema-level validation failures. On a 422 the client also does
`detail?.detail ?? response.statusText` where FastAPI's `detail` is a *list* of error
objects, so `ApiError.message` becomes `"[object Object]"`. Net effect: a 422 produces a
silent failure — the mutation rejects, no toast appears, the form clears (finding 7), and
the entry is gone. Handle both:

```ts
// client.ts
const detail = await response.json().catch(() => null)
const message = Array.isArray(detail?.detail)
  ? detail.detail.map((e: { msg: string }) => e.msg).join('; ')
  : (detail?.detail ?? response.statusText)
throw new ApiError(response.status, message)

// App.tsx
if (error instanceof ApiError && (error.status === 400 || error.status === 422)) {
  emitErrorToast(error.message)
}
```

---

### SUGGESTION

**9. N+1 query listing service entries, plus a missing index on the join column**
`backend/app/maintenance/service.py:84-86`, `backend/app/attachments/models.py:8`

`list_entries` runs one `SELECT` for the entries and then `_attachments_for(db, entry.id)`
per entry. `Attachment.service_entry_id` is declared `foreign_key=` but has no index —
SQLite does not index foreign keys automatically — so each of those N queries is a full
table scan. Small today; it grows with every invoice photo. Fetch once and group:

```python
def list_entries(db: Session) -> list[ServiceEntryRead]:
    entries = db.exec(select(ServiceEntry).order_by(ServiceEntry.date.desc())).all()
    by_entry: dict[int, list[Attachment]] = defaultdict(list)
    for a in db.exec(select(Attachment)).all():
        by_entry[a.service_entry_id].append(a)
    return [_to_read(e, by_entry[e.id]) for e in entries]
```

and add the index (needs an Alembic revision):

```python
service_entry_id: int = Field(foreign_key="serviceentry.id", index=True)
```

**10. Every fuel/service write loads the entire history twice**
`backend/app/car/service.py:51-52`, `backend/app/fuel/service.py:56-58`

`validate_mileage_consistency` does `SELECT *` over both `FuelEntry` and `ServiceEntry` on
every create and update, and `_consumption_for_entry` then re-reads all fuel entries again.
Only the nearest neighbour on each side of `entry_date` is actually needed:

```python
before = db.exec(
    select(func.max(FuelEntry.mileage_km)).where(FuelEntry.date < entry_date, ...)
).first()
```

Add `index=True` to `FuelEntry.date` and `ServiceEntry.date` while you are in a migration.
For a personal log this is a few hundred rows — file it as cleanup, not urgency.

**11. `get_summary` re-queries fuel entries it already has in hand**
`backend/app/dashboard/service.py:40, 64-68`

`fuel_entries` is loaded at line 40, then `list_entries_with_stats(db)` at line 66 issues
the same query again purely to reach the consumption figures. Folding finding 4's
distance-weighted helper in here removes the second read as a side effect.

**12. `date.fromordinal` arithmetic where `timedelta` is clearer**
`backend/app/reminders/service.py:90`

`base.fromordinal(base.toordinal() + reminder.recurrence_days)` calls a classmethod through
an instance to do what `base + timedelta(days=reminder.recurrence_days)` says directly.
Covered by the rewrite in finding 3.

**13. `useIsDark` is named like a hook, behaves like a snapshot**
`frontend/src/features/dashboard/FuelTrendChart.tsx:23-26`, `frontend/src/features/dashboard/CostBreakdownChart.tsx:14-17`

It calls no hooks and creates no subscription, so chart colours are whatever the OS theme
was at render time and never follow a live theme switch. The `use` prefix also invites the
lint rule to treat it as a hook. Duplicated verbatim across two files. Make it real and
share it from `src/lib/`:

```ts
export function useIsDark(): boolean {
  const [isDark, setIsDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (e: MediaQueryListEvent) => setIsDark(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return isDark
}
```

**14. `confirmDialog` hangs forever if nothing is listening**
`frontend/src/lib/confirmBus.ts:16-20`

`new Promise((resolve) => listeners.forEach(...))` never settles when `listeners` is empty
(and a second concurrent call silently drops the first host's `resolve`). Today
`ConfirmDialogHost` is always mounted in `App.tsx`, so this is latent — but a dangling
promise in a delete handler is an unpleasant thing to debug later. Resolve `false` when
there is no listener.

Related: attachment deletion (`AttachmentUploader.tsx:49`) fires immediately with no
confirmation, while every other destructive action in the app goes through `confirmDialog`.

**15. Unknown `/api/*` paths return `index.html` with a 200**
`backend/app/main.py:40-53`

The SPA catch-all is registered after the routers, so real endpoints win — but a typo'd or
retired API path falls through to the HTML fallback instead of a 404, which turns a
mistyped URL into a confusing JSON parse error on the client. The traversal guard here is
correct and should stay as-is. Add an early bail:

```python
if full_path.startswith(("api/", "auth/")):
    raise HTTPException(status_code=404, detail="Not found")
```

**16. `CLAUDE.md` and `TODO.md` describe editable exchange rates that no longer exist**
`CLAUDE.md` (Currency section), `TODO.md` item 5

Both state that rates are editable — "one editable `rate_to_czk`", "editing a rate in
Settings", "Inline, editable exchange rate on fuel/maintenance forms". In the current code
the rate inputs on `FuelForm.tsx:91-101` and `MaintenanceForm.tsx:104-114` are
`disabled readOnly`, `currencyApi` (`frontend/src/api/currency.ts`) exposes only `list`,
and `currency/router.py` has no `PUT` — rates come solely from the ČNB daily fixing, with
`update_rate` reachable only from `_ensure_rates_fresh`. The snapshot-at-entry-time
architecture note is still accurate and worth keeping; the editability claims are stale.
Either restore the edit path or correct the docs.

**17. `CarProfileUpdate` accepts any year**
`backend/app/car/schemas.py:12-16`

`year: int | None` is unbounded, so `year=999999` is stored and rendered into the dashboard
heading. A one-line guard matches the validation rigour applied elsewhere:

```python
year: int | None = Field(default=None, ge=1900, le=2100)
```

---

### Testing

Coverage is genuinely good — 52 tests, one file per domain, `client`/`anon_client`
fixtures against a fresh temp SQLite DB, and the ČNB fetch stubbed autouse so the suite
stays offline. The gaps line up with the bugs above, which is why they survived:

- `tests/test_reminders.py` — recurrence is only tested with both fields set. Add
  `test_completing_reminder_recurring_by_days_without_due_date` and the `recurrence_km` /
  no-`due_mileage_km` twin (finding 3).
- `tests/test_dashboard.py` — `avg_consumption_l_per_100km` is never asserted. Add
  `test_avg_consumption_is_distance_weighted` using the 1000 km @ 5 l + 100 km @ 20 l case
  above, expecting 6.36 rather than 12.5 (finding 4).
- `tests/test_attachments.py` — covers the happy path, the 404, and delete. Add rejection
  of an oversized upload and of a disallowed content type (finding 5).
- No test asserts a 422 body shape or that a rejected create leaves no row behind
  (finding 8).
- `tests/test_auth.py` exercises `is_email_allowed` both ways but nothing pins the
  session-secret requirement. Once finding 1 lands, add a test that constructing `Settings`
  without `CARSTATS_SESSION_SECRET` raises.
- No frontend test runner is configured, so findings 7, 8, 13 and 14 are unverifiable in
  CI. Not worth standing up Vitest for this app on its own, but worth knowing that the
  entire client is manual-test-only.
