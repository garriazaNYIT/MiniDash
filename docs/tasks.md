# Track C implementation slices

## Completed implementation

The original eight-slice plan was consolidated into six implementation slices. Lifecycle integration was combined with persistent status history, and ETA calculation was combined with transactional ETA persistence. The completed slices below supersede the original numbering and iteration notes.

All six slices are implemented and locally tested. The user ran the full pytest suite locally with **159 tests passing**. The user also completed a successful end-to-end demonstration using FastAPI, Swagger UI, the polling client, and the driver simulator: order #1 was created through Swagger, progressed from `PLACED` through `DELIVERED`, and displayed status and ETA changes in the polling terminal.

These full-suite and live-demo results are user-reported local verification. Codex's environment could run selected tests but could not collect the full API suite because FastAPI was unavailable; those environment limitations do not describe the user's successful local run.

## Implementation and verification criteria

| Slice | Deliverable and implementation boundary | Meaningful test criteria | State |
| --- | --- | --- | --- |
| 1. Lifecycle validation | Pure uppercase lifecycle policy in `app/order_tracking.py`; `PLACED -> PREPARING -> READY -> PICKED_UP -> DELIVERED`, cancellation only from `PLACED`, and successful same-status no-ops. | All 36 recognized state pairs; unknown/lowercase values; skipped and backward transitions; terminal states and repeated requests. | Implemented and locally tested |
| 2. Persistent status history and lifecycle integration | Integrate the shared policy into order creation, input validation, PATCH, and SQLite status constraints. Persist initial and transition history atomically with status using UTC timestamps and stable event ordering. | Initial `PLACED` event; every forward step; cancellation restrictions; 404/409/422 behavior; exactly one event per actual change; no duplicate events for repeats; invalid requests leave state/history unchanged; rollback, restart persistence, timestamp ties, and order isolation. | Implemented and locally tested |
| 3. Tracking API | Read-only `GET /orders/{id}/tracking` through routes, services, and repository. Return order ID, current status, and chronological history from a consistent SQLite snapshot; ETA fields were added in Slice 4. | Successful payload; 404 for missing orders; 422 for invalid IDs; history ordering including timestamp ties; repeated reads leave storage unchanged; persistence across application restarts and order isolation. | Implemented and locally tested |
| 4. ETA calculation and persistence | Validate and store customer-supplied distance. Calculate travel at 30 km/h rounded up to whole minutes, include remaining preparation for `PLACED`/`PREPARING`, and exclude preparation for `READY`/`PICKED_UP`. Persist ETA and update timestamp atomically with creation/status/history; expose ETA and derived remaining minutes in tracking. | 20-minute preparation plus 6 km equals 32 minutes; zero/fractional distance; missing, negative, nonfinite, and unsupported inputs; deterministic elapsed-time and phase calculations; actual delivery timestamp; cleared cancellation ETA; same-status and invalid requests preserve ETA; rollback and restart persistence. | Implemented and locally tested |
| 5. Live tracking polling client | Standard-library CLI accepting order ID and optional base URL; poll every two seconds, display changed tracking information, stop at delivery/cancellation or Ctrl+C, and handle missing orders and temporary failures. Polling reads tracking and never advances status. | Mocked HTTP responses and sleep; changed versus duplicate snapshots; status, ETA, and remaining-minute display; default interval; terminal stop; 404; connection/server failure recovery; malformed responses; Ctrl+C and CLI validation. | Implemented and locally tested |
| 6. Driver simulation | Standard-library CLI for an existing `PLACED` order with optional base URL and configurable delays. Check current status before each transition and PATCH through the full lifecycle. Stop on unexpected states or request failures; never edit SQLite directly or create an order. | Mocked GET/PATCH ordering and JSON bodies; configurable delays; wrong starting state; externally changed status; HTTP/network failures without retries; malformed responses and transition confirmation; Ctrl+C and CLI validation. Locally demonstrated alongside the polling client. | Implemented and locally tested |

The consistent-snapshot design remains part of the tracking boundary. A dedicated concurrent-update snapshot test was contemplated in the original plan; the local suite result alone is not a claim that this specific concurrency scenario was tested.

## Database compatibility decision

Legacy database migration was deliberately excluded in favor of resetting disposable development data. The user approved this approach, stopped the API, deleted the disposable development database, and restarted FastAPI to initialize the updated schema. No migration or invented historical backfill is claimed. Legacy/pre-ETA schema guards remain in place; preserving production or non-disposable legacy data would require separate migration work.

## Scope boundaries

The implementation preserves the Python/FastAPI/SQLite/pytest stack and routes/services/repository architecture. Each slice was handled separately with relevant automated tests. The clients use standard-library HTTP support; no new dependency declarations were introduced for them.

Real GPS/geocoding, traffic models, WebSockets/SSE, production frontend work, and legacy-data migration remain outside these six slices. This task record update changes documentation only and does not authorize additional implementation, commits, or pushes.
