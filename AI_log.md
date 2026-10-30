# MiniDash — AI Usage Log

## Entry 1 — Baseline Generation

**Date:** October 28, 2026

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Initial MiniDash baseline setup (before feature implementation)

**Prompt:** Used the baseline generation prompt from Appendix C of the assignment.

**What AI produced:** A FastAPI application with five REST endpoints, a layered architecture, SQLite storage, five seeded restaurants, automated pytest tests, and a README.

**What I verified:** Confirmed Python 3.12.8 was installed, installed the project dependencies, ran the automated test suite (17 tests passed), started the FastAPI server, and confirmed all five endpoints appeared in Swagger UI.

**What I changed and why:** No code changes documented at this stage. Codex initially reported that Python was unavailable, but I verified Python was installed and ran the tests manually.

**Outcome:** Baseline generated and verified. Ready for feature development.

## Entry 2 — Order Lifecycle Validation (Slice 1)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Order Lifecycle Validation (Slice 1)

**Task:** Implement the required order status lifecycle for Track C.

**What AI produced:** `app/order_tracking.py`, lifecycle tests, and initial planning documents.

**Design decisions:** Uppercase statuses, cancellation only from `PLACED`, and idempotent repeated status requests.

**What I verified:** Reviewed the transition validation code and ran pytest locally; 76 tests passed.

**Outcome:** Lifecycle validation implemented and verified.

### Substantially Revised AI Proposal #2 — Implementation Plan

Codex originally proposed eight implementation slices in `docs/tasks.md`. I revised that AI-generated implementation plan into six slices, combining related tasks such as lifecycle integration with persistent history and ETA calculation with ETA persistence. I retained separate testing and Git commits for each of the six implementation slices. I made this decision to reduce unnecessary overhead while preserving the assignment's requirements. I later updated `docs/tasks.md` to reflect the completed six-slice implementation. This was a revision to the implementation plan, not a rejection of generated code.

## Entry 3 — Persistent Order Status History (Slice 2)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Persistent Order Status History (Slice 2)

**Task:** Persist order status history in SQLite.

**What AI produced:** Changes to `repository.py`, `schemas.py`, `services.py`, and automated tests.

**What I verified:** Reviewed the database schema and service logic, confirmed that status changes and history entries share a transaction, and ran pytest locally with 89 tests passing.

**What I changed and why:** Approved resetting the development database rather than implementing legacy schema migration.

**Outcome:** Persistent timestamped status history implemented and verified.

### Rejected AI Proposal #1 — Legacy Database Migration

Codex raised migration of existing lowercase order statuses as a possible approach. I rejected implementing a migration because the project used disposable development data. I chose to reset the SQLite database and initialize the new uppercase schema instead. This avoided unnecessary migration code while meeting the assignment's lifecycle requirements. I later verified this decision by resetting the database and successfully running the application. Migration was proposed; no migration code was generated or rejected.

## Entry 4 — Order Tracking API (Slice 3)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Order Tracking API (Slice 3)

**Task:** Implement `GET /orders/{id}/tracking`.

**What AI produced:** Changes to `app/routes.py`, `app/services.py`, and `tests/test_api.py`.

**What I verified:** Reviewed the tracking service logic, confirmed it retrieves the current status and chronological history from SQLite, returns HTTP 404 for nonexistent orders, and performs read-only operations.

**Testing:** Ran the full pytest suite locally; 95 tests passed.

**Outcome:** Tracking API implemented and verified.

## Entry 5 — ETA Calculation (Slice 4)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** ETA Calculation (Slice 4)

**Task:** Implement estimated delivery time calculations using restaurant preparation time and delivery distance.

**What AI produced:** `app/eta.py`, updates to the repository, schemas, services, tracking response, and automated tests.

**Design decisions:** Fixed travel speed of 30 km/h, remaining preparation time based on elapsed time, and ETA recalculation on actual status changes.

**What I verified:** Reviewed the ETA implementation and tests, including status-dependent calculations and persistence. Ran pytest locally; 118 tests passed.

**AI output corrected:** Codex reported that the full test suite couldn't run because FastAPI was missing in its environment. I verified the complete suite locally and requested a correction to the documentation.

**Outcome:** ETA calculations implemented and verified.

## Entry 6 — Live Order Tracking via Polling (Slice 5)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Live Order Tracking via Polling (Slice 5)

**Task:** Implement live order tracking using a command-line polling client.

**What AI produced:** `scripts/poll_tracking.py` and `tests/test_poll_tracking.py`.

**Design decisions:** Use HTTP polling every two seconds instead of SSE or WebSockets to keep the implementation simple.

**What I verified:** Ran the full pytest suite locally with 133 tests passing. Later tested the polling client against the running FastAPI server and confirmed it detected status and ETA changes.

**Outcome:** Live tracking implemented and verified.

## Entry 7 — Driver Simulation (Slice 6)

**Tool:** OpenAI Codex, VS Code extension

**Slice:** Driver Simulation (Slice 6)

**Task:** Implement a driver simulator that advances orders through the complete delivery lifecycle.

**What AI produced:** `scripts/simulate_driver.py`, `tests/test_simulate_driver.py`, and `scripts/README.md`.

**Design decisions:** Simulate the full lifecycle from `PLACED` to `DELIVERED`, with configurable delays.

**What I verified:** Ran the full pytest suite locally; 159 tests passed. Then ran the simulator against the live FastAPI server and confirmed it advanced order #1 through all five statuses.

**Outcome:** Driver simulation implemented and verified through automated tests and a successful end-to-end demonstration.

## Entry 8 — End-to-End Integration and Database Reset

**Tool:** OpenAI Codex, VS Code extension, with ChatGPT-assisted troubleshooting.

**Task:** Verify that the complete MiniDash tracking system works together.

**Issue encountered:** The API failed to start because the existing SQLite database still used the original lowercase status schema, which was incompatible with the new Track C schema.

**What I changed and why:** Stopped the API, deleted the disposable development database, and restarted FastAPI so SQLite could initialize the updated schema. This followed the previously approved decision to reset development data rather than implement a migration.

**What I verified:** Created order #1 through Swagger UI, started the polling client, ran the driver simulator, and confirmed that the order advanced from `PLACED` through `DELIVERED`, with ETA updates visible in the polling terminal.

**Outcome:** The database compatibility issue was resolved and the full workflow passed an end-to-end demonstration.
