# Track C: Live Order Tracking — Implementation Tasks and AI-Assisted Workflow

## Project Overview

MiniDash is a food-delivery REST API built using Python, FastAPI, SQLite, and pytest. For the CSCI-665 Software Engineering midterm, I selected Track C: Live Order Tracking.

The goal was to allow customers to follow an order from placement through delivery, view timestamped status changes, and receive an estimated delivery time. The implementation also required a polling client and a driver simulation to demonstrate the feature working end to end.

I used OpenAI Codex in VS Code as my AI pair programmer. My role was to define the requirements, direct the implementation, review the generated code, make design decisions, and independently verify the results.

## Development Approach and Prompting Strategy

I started by having Codex inspect the existing application structure before implementing anything. The goal was to understand how the routes, services, repository, database, and tests were organized.

My instructions throughout development emphasized the following:

- Preserve the existing FastAPI, SQLite, and pytest technology stack.
- Maintain separation between API routes, business logic, and database operations.
- Implement one feature slice at a time rather than generating the entire feature at once.
- Follow the requirements and acceptance criteria in `docs/requirements.md`.
- Generate automated tests for each implementation slice, including invalid inputs and boundary cases.
- Avoid introducing unnecessary dependencies or unrelated changes.
- Explain implementation decisions and identify files being changed.
- Do not automatically commit or push changes without approval.
- Verify completed work before moving to the next slice.

As development progressed, I became more specific about implementation boundaries, expected behavior, and testing requirements.

Rather than simply asking Codex to build live order tracking, I directed it to implement individual components that could be reviewed and tested independently.

## Implementation Plan

The original AI-generated plan contained eight slices. I substantially revised it into six implementation slices to better reflect the actual development workflow.

Lifecycle integration was combined with persistent status history, while ETA calculation was combined with transactional ETA persistence.

All six slices were implemented, tested locally, and committed separately.

### Slice 1 — Order Lifecycle Validation

**Objective:** Implement the order status lifecycle as reusable business logic.

The required progression was:

`PLACED → PREPARING → READY → PICKED_UP → DELIVERED`

Cancellation was allowed only from `PLACED`. Invalid transitions had to be rejected, and repeated requests for the current status had to succeed without changing anything.

**Implementation:**
- Created `app/order_tracking.py`.
- Defined uppercase order statuses using an enum.
- Implemented transition validation independent of the database.
- Supported successful same-status no-ops.
- Rejected skipped, backward, unknown, and terminal-state transitions.

**Verification:**

Tested all 36 recognized status pairs, invalid values, cancellation restrictions, and repeated requests.

**Result:** 76 automated tests passing after this slice.

### Slice 2 — Persistent Status History and Lifecycle Integration

**Objective:** Integrate lifecycle validation into the API and persist every actual status change.

**Implementation:**
- Integrated lifecycle validation with order creation and status updates.
- Updated SQLite status constraints.
- Added persistent order status history.
- Recorded UTC timestamps for status events.
- Ensured status and history updates occur atomically.
- Prevented duplicate history entries for repeated status requests.

**Verification:**

Tested initial `PLACED` events, valid transitions, cancellation, invalid requests, HTTP error behavior, rollback, restart persistence, timestamp ordering, and order isolation.

**Result:** 89 automated tests passing.

### Slice 3 — Order Tracking API

**Objective:** Provide a read-only endpoint for customers to retrieve order progress.

**Implementation:**

Added:

`GET /orders/{id}/tracking`

The endpoint returns the order ID, current status, and chronological status history.

The implementation follows the existing routes, services, and repository architecture and reads tracking information from a consistent SQLite snapshot.

**Verification:**

Tested successful tracking responses, missing orders, invalid IDs, chronological ordering, repeated reads, persistence, and order isolation.

**Result:** 95 automated tests passing.

### Slice 4 — Delivery ETA Calculation and Persistence

**Objective:** Calculate and persist estimated delivery times based on restaurant preparation time and delivery distance.

**Implementation:**
- Added customer-supplied delivery distance.
- Used a simplified travel speed of 30 km/h.
- Rounded travel estimates up to whole minutes.
- Included remaining preparation time during `PLACED` and `PREPARING`.
- Used travel time only during `READY` and `PICKED_UP`.
- Updated ETA information when order status changed.
- Recorded actual delivery time at `DELIVERED`.
- Cleared the ETA for cancelled orders.
- Persisted ETA changes transactionally with status and history.

**Verification:**

A restaurant with a 20-minute preparation time and a delivery distance of 6 km produces an initial ETA of 32 minutes.

Additional tests covered invalid distances, fractional values, elapsed time, lifecycle phases, cancellation, idempotency, rollback, and restart persistence.

**Result:** 118 automated tests passing.

### Slice 5 — Live Tracking Polling Client

**Objective:** Allow customers to observe order progress without manually refreshing the tracking endpoint.

**Implementation:**
- Created `scripts/poll_tracking.py`.
- Used Python standard-library HTTP functionality.
- Accepted an order ID and optional API base URL.
- Polled the tracking endpoint every two seconds.
- Displayed changes in status, ETA, and remaining time.
- Avoided repeating identical tracking information.
- Stopped automatically when an order reached `DELIVERED` or `CANCELLED`.
- Handled HTTP errors, connection failures, and keyboard interruption.

The polling client only reads tracking information. It never changes an order's status.

**Verification:**

Tested mocked HTTP responses, duplicate snapshots, terminal states, missing orders, temporary failures, malformed responses, and CLI validation.

**Result:** 133 automated tests passing.

### Slice 6 — Driver Simulation

**Objective:** Simulate a driver progressing an existing order through the complete lifecycle.

**Implementation:**
- Created `scripts/simulate_driver.py`.
- Accepted an existing order ID, optional API base URL, and configurable delays.
- Verified the order's current status before making changes.
- Used the existing API to advance statuses.
- Progressed through `PREPARING`, `READY`, `PICKED_UP`, and `DELIVERED`.
- Stopped when an unexpected status or request failure occurred.
- Avoided directly modifying SQLite or creating new orders.

**Verification:**

Tested request ordering, PATCH bodies, configurable delays, invalid starting states, unexpected changes, HTTP/network failures, malformed responses, and interruption handling.

**Result:** 159 automated tests passing.

## End-to-End Integration Testing

After completing all six slices, I performed a live integration test using the actual application.

The process was:

1. Started the FastAPI application.
2. Created an order through Swagger UI.
3. Confirmed the order began in `PLACED` with an initial ETA.
4. Started the polling client in a separate terminal.
5. Started the driver simulation in another terminal.
6. Observed the order advance through all required statuses.
7. Verified that status history and ETA information updated.
8. Confirmed the polling client stopped automatically when the order was delivered.

The demonstration successfully progressed order #1 from `PLACED` through `DELIVERED`.

The final locally executed test suite contained **159 passing tests**.

These results represent local verification. Codex encountered limitations in its own execution environment and could not run the complete FastAPI test suite, so I independently ran the tests on my computer.

## AI Output Review and Design Decisions

### 1. Revised Implementation Plan

Codex initially proposed an eight-slice implementation plan.

I revised the plan to six slices by consolidating closely related work. This allowed me to keep the implementation organized while avoiding unnecessary separation between components that needed to be integrated together.

The revised plan became the basis for the six feature commits.

### 2. Rejected Legacy Database Migration

During development, the original database schema conflicted with the updated lifecycle and ETA requirements.

Codex proposed supporting legacy database migration.

I rejected that approach because the database contained disposable development data, not production information.

Instead, I stopped the API, deleted the development database, and restarted FastAPI to initialize the updated schema.

This avoided unnecessary migration code and kept the implementation focused on the assignment requirements.

No legacy migration or historical data backfill was implemented.

### 3. Independently Verified AI Test Reports

Codex repeatedly reported that it could not execute the full test suite because its environment lacked required Python dependencies, including FastAPI.

I verified this independently by running pytest in my local development environment.

The full suite passed locally, eventually reaching 159 tests.

This reinforced the importance of distinguishing an AI tool's environment limitations from actual application defects.

### 4. Reviewed and Updated Documentation

As implementation progressed, some documentation no longer accurately reflected the completed work.

I directed Codex to revise `docs/tasks.md` so it described the six implemented slices rather than the original eight pending tasks.

The updated documentation records completed functionality and verified results without claiming that untested scenarios were verified.

## Verification Boundaries

Although the application passed 159 automated tests and the live end-to-end demonstration succeeded, these results do not prove every possible production scenario.

A dedicated concurrent-update test of the tracking endpoint's consistent SQLite snapshot was considered but was not specifically verified.

Other areas that would require additional work or testing include production-scale concurrent requests, real-world delivery distances, GPS integration, traffic-based ETA calculations, and production deployment behavior.

The implementation intentionally uses a simplified distance model rather than a real mapping service.

## Scope and Architecture

The completed project preserves the original Python, FastAPI, SQLite, and pytest stack.

The application maintains separation between:

- **Routes:** HTTP endpoints and request handling.
- **Services:** Business logic and lifecycle rules.
- **Repository:** SQLite persistence and data retrieval.
- **Tracking logic:** Order transitions and ETA calculations.
- **Client scripts:** Polling and simulated driver activity.

Real GPS/geocoding, traffic modeling, WebSockets, server-sent events, a production frontend, and legacy database migration were excluded from the six required slices.

No additional third-party dependencies were introduced for the polling client or driver simulator.

## Final Outcome

The project successfully implemented Track C: Live Order Tracking.

All six implementation slices were completed and locally verified, with 159 passing automated tests and a successful end-to-end demonstration.

The development process also demonstrated the role of AI-assisted software engineering. Codex accelerated implementation and test generation, but I remained responsible for system design, implementation boundaries, reviewing AI output, selecting appropriate solutions, and verifying that the finished application worked correctly.