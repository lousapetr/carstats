# TODO — next session

Five items, planned but not started. Implement one at a time, in this order
(roughly easiest/most isolated first). Each is independently shippable/
committable.

## 1. Proper PWA home-screen icon (Android / Nova Launcher)

`frontend/public/favicon.svg` is already a red-car glyph, and
`frontend/vite.config.ts`'s `manifest.icons` currently declares only:
```
{ src: 'favicon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }
```
That's almost certainly why it looks bad once added to an Android home
screen: Chrome/Android's "Add to Home Screen" wants a **maskable** PNG icon
to render properly in adaptive-icon launchers like Nova — an SVG-only, non-
maskable manifest icon often falls back to a generic/cropped/screenshot-
derived icon instead.

Plan:
- Design (or touch up) the car icon with a maskable-safe variant: the
  existing design is not full-bleed (has transparent background + margin),
  so needs a second version filling the full square with safe padding for
  circular/adaptive crops (see the existing code comment in
  `vite.config.ts` explaining why "any"-only was chosen previously).
- Export PNGs at 192×192 and 512×512 for both `any` and `maskable` purpose
  (4 files, or 2 if reusing the same image for both purposes where the
  design already has enough padding).
- Add them under `frontend/public/` and reference all four in
  `manifest.icons` in `vite.config.ts`.
- Rebuild, then actually test by removing and re-adding the PWA on the
  phone (Android caches the icon at install time — a redeploy alone won't
  update an already-installed icon).

## 2. Add "Aditiva" as a maintenance type

Straightforward enum addition, touches both backend and frontend in
parallel — no shared logic to design, just enumerate the type in ~6 places:

- `backend/app/maintenance/models.py` — add to `ServiceType` StrEnum (no
  migration needed: SQLite stores it as plain TEXT with no CHECK
  constraint, confirmed no enum constraint in `backend/alembic/versions/`).
- `backend/app/dashboard/service.py` — add to `SERVICE_TYPE_LABELS_CS`.
- `frontend/src/types/index.ts` — add to the `ServiceType` union.
- `frontend/src/features/maintenance/MaintenanceForm.tsx` — add to the zod
  enum and the `SERVICE_TYPES` options array (label list).
- `frontend/src/features/maintenance/MaintenanceLogPage.tsx` — add to its
  own label map.
- `frontend/src/features/dashboard/CostBreakdownChart.tsx` — add a
  color+label entry so it gets its own slice/legend color instead of
  falling through unstyled.

Confirm exact Czech label wording before implementing — "Aditiva" (plural,
as the user wrote) vs. "Aditivum" (singular, matches the grammatical
pattern of "Výměna oleje"/"Servis motoru" less, but matches "Pneumatiky"
being plural too) — either is fine, just pick one and use it consistently
across all the places above.

## 3. Partial tank fill-ups break consumption calculation

Root cause: `backend/app/fuel/service.py`'s `_consumption_since_previous`
and `list_entries_with_stats` compute L/100km from *just the immediately
preceding entry's mileage delta*, assuming every fill-up tops the tank
back to full. A partial fill breaks that assumption — the liters bought
don't correspond to the full distance since the last fill.

The user's suggested fix (a "was it a full tank?" checkbox, default
checked, hide consumption when unchecked) is directionally right but
under-uses the data: the standard/better approach used by fuel-log apps is
**full-to-full accounting** — consumption is only computed when the
*current* entry is a full tank, as the sum of liters across all entries
back to (and not including) the *previous* full-tank entry, divided by the
mileage delta between those two full-tank points. This correctly handles
one or more partial fills in between, instead of just hiding them.

Recommend implementing it this way rather than the literal ask. Plan:

- **Migration**: add `full_tank: bool = True` (`Field(default=True)`) to
  `FuelEntry` in `backend/app/fuel/models.py`; new alembic revision
  (`uv run alembic revision --autogenerate -m "add full_tank to fuel entries"`).
- **Schemas** (`backend/app/fuel/schemas.py`): add `full_tank: bool = True`
  to `FuelEntryCreate`; it already flows into `FuelEntryRead` via
  inheritance.
- **Service** (`backend/app/fuel/service.py`): rework
  `list_entries_with_stats` to walk entries oldest-first tracking a
  running liters-sum since the last full-tank entry; when the current
  entry has `full_tank=True`, emit
  `consumption = running_liters / (current.mileage_km - last_full_tank.mileage_km) * 100`
  then reset the running sum and advance `last_full_tank`; when
  `full_tank=False`, add its liters to the running sum and emit
  `consumption=None`. Apply the equivalent logic to
  `_consumption_since_previous` (used by `create_entry`/`update_entry` for
  the single just-written entry) — probably simplest to just have both
  paths call one shared helper instead of keeping two implementations in
  sync.
- **Frontend**: `FuelForm.tsx` — add a checkbox `full_tank` (default
  checked, per the user's ask) to the zod schema and form. `FuelLogPage.tsx`
  — decide how to surface partial fills in the list (e.g. a small badge)
  and confirm consumption legitimately shows blank/dash for partial-fill
  rows. Dashboard's `FuelTrendChart.tsx`/`get_fuel_trend` need no change —
  they already just plot whatever `consumption_l_per_100km` comes back
  (`null` points are already filtered in `ConsumptionTrendChart`).
- Check `car/service.py`'s `validate_mileage_consistency`/
  `recalculate_current_mileage` — unaffected, they only care about
  `mileage_km`, not fuel volume.

Confirm with the user whether they're fine with the full-to-full approach
before implementing, since it changes behavior/data shown for *existing*
entries too (all currently show `full_tank=True` after the migration
default, so nothing changes for already-logged full fills — only new
partial entries going forward affect anything).

## 4. Show price-per-liter on the "Cena paliva v čase" dashboard chart

Good news: the data already exists end-to-end —
`FuelTrendPoint.price_per_liter` (CZK-converted) is already returned by
`backend/app/dashboard/service.py`'s `get_fuel_trend()` and typed in
`FuelTrendPoint`. This is purely a frontend change:

- `frontend/src/features/dashboard/FuelTrendChart.tsx` —
  `FuelPriceTrendChart` currently only renders one `<Line dataKey="price_total">`.
  Add a second line for `price_per_liter`, most likely on a **second Y
  axis** (`yAxisId`) since totals (hundreds/thousands of Kč) and
  price-per-liter (tens of Kč) are on very different scales and would
  otherwise flatten one line. Recharts supports this via two `<YAxis>`
  elements with matching `yAxisId` props on the `<Line>`s. Add a distinct
  color (extend `CHART_COLORS`) and a legend so the two lines are
  distinguishable, and extend the `Tooltip formatter` to label both
  values.

## 5. Inline, editable exchange rate on fuel/maintenance entry forms

Currently `backend/app/currency/service.py`'s `get_rate()` is the only
source of the exchange rate used when creating/updating an entry —
`fuel/service.py::create_entry`/`update_entry` and the equivalent in
`maintenance/service.py` always call it, silently, with no way to override
per-entry. The user wants the rate visible and editable right on the
Fuel/Maintenance form when a non-CZK currency is selected, seeded from the
current Settings default, and — if the user edits it there — that edit
should also update the Settings default (`CurrencyRate.rate_to_czk`) for
future entries, not just this one entry's snapshot.

Plan:
- **Backend schemas**: add `exchange_rate: float | None = None` to
  `FuelEntryCreate` (`backend/app/fuel/schemas.py`) and
  `ServiceEntryCreate` (`backend/app/maintenance/schemas.py`) — `None`
  means "use the current default," matching today's behavior for CZK/
  unedited cases.
- **Backend service** (`fuel/service.py::create_entry`/`update_entry`, and
  the mirror in `maintenance/service.py`): if `data.exchange_rate` is
  provided and differs from the currency's current default, call
  `currency.service.update_rate(db, data.currency, data.exchange_rate)`
  *and* use that value as the entry's snapshot; otherwise keep calling
  `get_rate()` as today. Keep `currency/service.py::update_rate` itself
  unchanged — it already does exactly what's needed
  (upserts `CurrencyRate.rate_to_czk`).
- **Frontend** (`FuelForm.tsx`, `MaintenanceForm.tsx`): both need the
  current rates list (`currencyApi.list`, already used in
  `SettingsPage.tsx` — reuse the same TanStack Query key `['currency-rates']`
  so it's cache-shared, not a duplicate fetch). When `currency !== 'CZK'`,
  show a rate input next to the currency dropdown, defaulting to that
  currency's current `rate_to_czk`, editable, included in the submitted
  payload as `exchange_rate`. Needs the `useForm<Input, unknown, Output>`
  three-generic pattern already used in these forms (per
  `CLAUDE.md`) since it's another `z.coerce.number()` field.
- Note this only affects *new* entries going forward — existing entries
  keep their already-snapshotted `exchange_rate`, consistent with the
  "snapshot at entry time" design documented in `CLAUDE.md`.
