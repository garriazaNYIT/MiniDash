# Track C: Live Order Tracking

## Purpose and existing system

Provide live order progress and an estimated delivery time for the CSCI-665 MiniDash assignment. This document defines the target behavior. Implementation is authorized one slice at a time; this iteration implements only slice 1 in `docs/tasks.md`.

Inspected sources: `AGENTS.md`, `README.md`, `app/main.py`, `app/routes.py`, `app/services.py`, `app/repository.py`, `app/schemas.py`, `tests/test_api.py`, and `requirements.txt`.

The existing Python/FastAPI/SQLite/pytest application separates routes, services, and repository code. Its lifecycle is `pending -> preparing -> out_for_delivery -> delivered`, with cancellation from both `pending` and `preparing` and successful same-status requests. SQLite constrains these existing status values. Restaurants already expose `avg_prep_minutes`; orders contain an address and UTC creation timestamp, but no distance, status history, or ETA. There is no tracking endpoint or polling client.

Preserve the routes/services/repository architecture. Future work must proceed in small implementation slices with proposed changes explained first, relevant feature and edge-case tests run afterward, and no new dependencies without approval. Never automatically commit or push.

## User stories

- As a customer, I want to poll my order's tracking information so I can see its latest status and expected delivery time.
- As a customer, I want to cancel an order before preparation starts so that an order already being prepared cannot be cancelled.
- As a customer, I want a timestamped status history so I can understand when my order progressed.
- As a restaurant operator, I want orders to progress through preparation and readiness in the required sequence.
- As a driver, I want to record pickup and delivery so customers see delivery progress and revised estimates.
- As an assignment demonstrator, I want a driver simulation script so I can demonstrate tracking updates without a real driver integration.

## Required lifecycle

Normal progression is exactly `PLACED -> PREPARING -> READY -> PICKED_UP -> DELIVERED`. Cancellation is allowed only from `PLACED`, before `PREPARING`, and results in a terminal cancellation status (`CANCELLED`). `DELIVERED` and cancellation are terminal. Skipping stages, moving backward, and leaving a terminal state are invalid. Repeated requests for the current status succeed without modifying history or ETA. Uppercase values are the target API contract; existing-data migration remains open below.

## EARS acceptance criteria

Approved decisions are binding. Details explicitly marked conditional remain pending and must be resolved before their implementation slice.

1. **AC-01 — Creation:** When a valid order is created, the system shall initialize its status to `PLACED` and persist exactly one timestamped `PLACED` history event.
2. **AC-02 — Forward progression:** When a request advances an order to the immediately following status in the required lifecycle, the system shall accept the transition and expose the new status on subsequent order and tracking reads. Each of the four forward transitions shall be independently testable.
3. **AC-03 — Early cancellation:** While an order is `PLACED`, when cancellation is requested, the system shall accept cancellation and record a timestamped cancellation event.
4. **AC-04 — Late cancellation:** If cancellation is requested while an order is `PREPARING`, `READY`, `PICKED_UP`, or `DELIVERED`, then the system shall reject the request without changing its status, history, or ETA.
5. **AC-05 — Invalid transitions:** If a request skips a stage, moves backward, or leaves a terminal state, then the system shall reject it without changing persisted order state, history, or ETA. Recognized but invalid transitions shall return HTTP 409 and unrecognized status values shall return HTTP 422.
6. **AC-06 — History integrity:** When a status change succeeds, the system shall atomically persist the new status, exactly one history event, and its recalculated ETA, so a failed operation persists none of these changes. History shall survive application restart, retain prior events, and expose UTC timestamps in chronological event order with stable ordering when timestamps tie.
7. **AC-07 — Tracking read:** When `GET /orders/{id}/tracking` is requested for an existing order, the system shall return HTTP 200 with the order identifier, current status, ordered timestamped history, and ETA information from a consistent snapshot. When the order does not exist, the system shall return HTTP 404. Reading tracking shall not mutate order state or append history.
8. **AC-08 — Initial ETA:** When an order is placed with valid distance-model inputs, the system shall calculate an ETA using the restaurant's preparation time and the approved simple distance model. A 20-minute preparation time and 6 km distance at 30 km/h shall produce a 32-minute initial estimate.
9. **AC-09 — ETA recalculation:** When any accepted status change occurs, the system shall recalculate the ETA using the new phase and its timestamp. Conditional on D4, `READY` and `PICKED_UP` shall include no remaining preparation time, `DELIVERED` shall have zero remaining duration with its delivery timestamp, and cancellation shall have no delivery ETA. Rejected transitions shall preserve the previous ETA.
10. **AC-10 — Polling updates:** While an order is active, when a polling client requests tracking after a committed status change, the system shall return the updated status, history, and ETA. The command-line demonstration client shall poll every two seconds and display each successful snapshot. Proposed terminal behavior, pending D5 approval, is to stop after observing delivery or cancellation; a transient request failure shall not be displayed as a status change.
11. **AC-11 — Driver simulation:** When the full-lifecycle driver simulation is run for a `PLACED` order, the script shall submit `PREPARING`, `READY`, `PICKED_UP`, and `DELIVERED` in that order using the existing status API, so a separate polling client can observe the changes. If the API rejects a transition or a request fails, then the script shall report the error and stop without claiming success or directly modifying SQLite. Script configuration and wrong-start behavior remain subject to D6.
12. **AC-12 — Persistence and isolation:** When an order is retrieved after application restart, the system shall retain its latest status and history. When one order progresses, the system shall leave other orders' statuses, histories, and ETAs unchanged.

Future pytest coverage must include the full lifecycle, cancellation at every phase, skipped and backward transitions, terminal states, missing orders, unknown status values, same-status no-op behavior, history ordering and persistence, failed-operation atomicity, deterministic ETA examples and boundaries, repeated tracking reads, polling visibility, and simulation failures.

## Established decisions

- Use uppercase `PLACED`, `PREPARING`, `READY`, `PICKED_UP`, `DELIVERED`, and terminal `CANCELLED`; cancellation is allowed only from `PLACED`.
- Repeated requests for the current status succeed with no history or ETA changes, including terminal statuses.
- Keep `PATCH /orders/{id}/status`; add `GET /orders/{id}/tracking`.
- Return 404 for missing orders, 409 for recognized invalid transitions, and 422 for invalid inputs or unknown status values.
- Calculate ETA from restaurant preparation time and a customer-supplied delivery distance at 30 km/h. For 20 minutes preparation and 6 km, the initial estimate is 32 minutes.
- Use a command-line polling client with a two-second interval.
- Provide a full-lifecycle simulation covering `PLACED -> PREPARING -> READY -> PICKED_UP -> DELIVERED` through the API.

## Remaining decisions requiring approval

These details are unresolved; do not silently select them in later slices. None blocks the isolated lifecycle policy in slice 1.

- **D1 - Existing data:** The existing SQLite constraint accepts lowercase statuses, and a local database exists. Approve migration and client compatibility policy before integrating uppercase statuses. Suggested mappings are `pending -> PLACED`, `preparing -> PREPARING`, `out_for_delivery -> PICKED_UP`, `delivered -> DELIVERED`, and `cancelled -> CANCELLED`. Do not invent missing historical events or timestamps. Approve how legacy history and distance are represented.
- **D3 - Tracking payload:** Proposed fields are `order_id`, `status`, `history` (entries with `status` and `changed_at`), `estimated_delivery_at`, `remaining_minutes`, and `eta_updated_at`. Approve names, timestamp precision, and whether remaining duration is derived at read time from a stored estimate.
- **D4 - ETA details:** Proposed input is a required finite, nonnegative `delivery_distance_km`, stored per order. Approve validation limits and existing-order handling. Speed is approved at 30 km/h; rounding and phase semantics remain open. Proposed travel duration is `ceil(distance_km / 30 * 60)` minutes. Proposed preparation remainder is `max(0, avg_prep_minutes - elapsed_minutes_since_anchor)`, anchored to placement until `PREPARING`, then to that event. Proposed `READY` and `PICKED_UP` estimates use full travel duration from the event time; delivery uses its actual timestamp and zero remaining duration, cancellation a null ETA. Approve these anchors, terminal values, rounding, and whether preparation time is snapshotted. Recalculate on actual changes only.
- **D5 - Polling errors:** CLI and two-second polling are approved. Proposed terminal behavior is to stop at delivery/cancellation. Approve request timeout, retry count for transient failures, and immediate failure on a missing order. Polling must not advance statuses.
- **D6 - Simulation configuration:** Full-lifecycle simulation is approved. Propose accepting base URL, order ID, and configurable delays, requiring an existing `PLACED` order, and failing immediately for a different starting state. Approve defaults and whether the script should optionally create its own order.
- **D7 - Rubric:** No separate assignment rubric is available. Any additional mandated formula, naming, or demonstration constraints require clarification.

## Out of scope

- Implementation of subsequent slices in this iteration; schema migration execution and dependency installation without approval.
- Real GPS tracking, geocoding, maps, traffic services, route optimization, and external delivery integrations.
- WebSockets, server-sent events, push notifications, and background automatic status progression in the API.
- Driver assignment, authentication/authorization, payments/refunds, multiple delivery stops, and restaurant-hours enforcement.
- A production frontend or production-scale polling infrastructure; the approved demonstration surface is a command-line client.
- Predictive ETA models, actual driver movement, and guaranteed delivery times.
- Automatic Git commits or pushes.
