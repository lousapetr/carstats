# TODO

Nothing queued right now — add new items here as they come up.

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
