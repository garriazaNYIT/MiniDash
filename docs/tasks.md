# Track C implementation slices

## Current iteration: Persistent Order Status History

The latest user request names this work Slice 2 and explicitly includes lifecycle integration and persistent history (rows 2 and 3 of the original plan below). That explicit scope supersedes the previous iteration authorization text. Implemented uppercase schema/input validation, shared lifecycle policy integration, and atomic UTC history writes. No tracking endpoint, ETA, polling, or simulation is implemented.

Legacy schemas are rejected before initialization writes anything, with an actionable error directing users to a new `MINIDASH_DB` path. Existing data is not migrated or backfilled; D1 remains unresolved. Existing order response fields are unchanged; history is available through the repository for later tracking work. Events are ordered by insertion ID, preserving transition order even for equal timestamps.

Verification: created a local `.venv` and installed the existing pytest dependency. Installing the existing requirements failed because MSYS Python 3.14 cannot build `pydantic-core` on its platform. The full suite was attempted and failed during collection with missing `fastapi`; API tests therefore remain unverified. Lifecycle and repository suites passed: **63 passed**, with one existing iterator-parametrization deprecation warning. SQLite tests verify restart persistence, tied-timestamp ordering, transaction rollback, and non-destructive legacy-schema rejection. API tests were added for lifecycle history, repeated/invalid requests, UTC timestamps, order isolation, and injected history-write failures, but cannot execute in this environment until FastAPI is available. No dependency declarations changed and no commit or push was made.

## Original slice plan and previous iteration record

Only slice 1 is authorized for implementation in this iteration. Each later slice requires its own proposed-change explanation, tests, and relevant regression checks. Resolve the cited approval items before dependent work; add no dependencies without approval.

| Slice | Deliverable and boundary | Independent verification | Prerequisites | State |
| --- | --- | --- | --- | --- |
| 1 | Pure uppercase lifecycle policy; no API or SQLite changes | All 36 state pairs; unknown/lowercase values; terminal no-ops | Approved lifecycle | Implemented; pytest verification blocked by environment |
| 2 | Integrate policy into creation, Pydantic validation, PATCH, and SQLite status constraints; handle existing data according to approved policy | Create PLACED; every forward step; cancel only PLACED; repeat no-op; 404/409/422; persistence and approved migration behavior | 1; D1 approval | Pending |
| 3 | Persist timestamped initial and transition history atomically with status | Exactly one event per real change; UTC and tie ordering; no-op/invalid requests add none; rollback, restart, and order isolation | 2; legacy-history policy in D1 | Pending |
| 4 | Validate/store delivery distance and implement deterministic preparation-plus-distance ETA calculation | 20-minute prep plus 6 km equals 32 minutes; zero/fractional distance; reject missing/negative/nonfinite/out-of-range inputs; approved rounding and phase boundaries | 2; D4 approval | Pending |
| 5 | Recalculate/persist ETA in creation and status transactions | Per-phase deterministic clock tests; terminal ETA; same-status and invalid requests preserve all ETA fields; rollback leaves status/history/ETA unchanged | 3, 4; D3/D4 approval | Pending |
| 6 | Add read-only GET /orders/{id}/tracking with consistent snapshot | 200 payload; 404 missing; 422 invalid ID; ordered history; repeat reads do not mutate; restart and concurrent-update snapshot tests | 5; D3 approval | Pending |
| 7 | CLI tracking poller, two-second interval | Fake HTTP/clock tests for repeated GET, displaying updates, interval, terminal stop, missing order and transient errors under approved policy | 6; D5 approval | Pending |
| 8 | Full-lifecycle driver simulation via PATCH | Fake HTTP/clock tests for PREPARING, READY, PICKED_UP, DELIVERED ordering and delays; rejected/network request stops; approved starting-state checks; API demonstration test | 2, 6; D6 approval | Pending |

## Iteration verification

- Added `app/order_tracking.py` and `tests/test_order_tracking.py` only for slice 1. No API, service, repository, database, or dependency changes.
- `python -m pytest -q` was attempted: the default MSYS Python has no pytest (or pip). `python3.12 -m pytest -q` was also attempted: its launcher points to missing `C:\Python312\python.exe`. No working alternative environment was found in the checked locations.
- A standard-library fallback check passed all 36 recognized state pairs, 21 invalid-input cases, vocabulary, and enum acceptance checks. This does not replace running the automated pytest suite or verify API regressions.
- `git diff --check` passed. Full pytest execution remains required in an environment with the existing project dependencies; no dependencies were installed.
- Later acceptance criteria are planned above, not claimed as complete. No subsequent slice was implemented; no commit or push was performed.
