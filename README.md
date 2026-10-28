# MiniDash

A small food-delivery REST API built with Python 3.10+, FastAPI, and SQLite.
The only direct dependencies are FastAPI, Uvicorn, and pytest. SQLite uses
Python's standard library; Pydantic is supplied by FastAPI.

## Run

From the project root on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000. Interactive documentation: http://127.0.0.1:8000/docs.
Startup creates `minidash.db` and idempotently seeds five restaurants with two
menu items each. Set `MINIDASH_DB` to a different SQLite file path if desired
(its parent directory must exist). File-backed databases are required.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/restaurants` | List restaurants, including opening hours and preparation time |
| GET | `/restaurants/{id}/menu` | List a restaurant's menu |
| POST | `/orders` | Create an order; returns 201 |
| GET | `/orders/{id}` | Retrieve an order and its items |
| PATCH | `/orders/{id}/status` | Update status and return the order |

Example POST `/orders` body:

```json
{
  "restaurant_id": 1,
  "address": "123 Main Street",
  "items": [
    {"menu_item_id": 1, "quantity": 2},
    {"menu_item_id": 2, "quantity": 1}
  ]
}
```

The server calculates `total_cents` (2900 for this example), snapshots each
item's unit price, assigns `pending` status, and stores a UTC `created_at`.
Items must belong to the selected restaurant; quantities must be positive
integers, the address must contain non-whitespace text, and repeated menu
items must be combined using quantity. Restaurant hours are informational.

Example PATCH `/orders/1/status` body:

```json
{"status": "preparing"}
```

Lifecycle: `pending` → `preparing` → `out_for_delivery` → `delivered`.
Cancellation is allowed from `pending` or `preparing`. Repeating the current
status succeeds. Delivered and cancelled orders cannot move to another status.
Missing resources return 404; invalid input returns 422; invalid transitions
return 409. Order creation and status changes use database transactions.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

On macOS/Linux, use `.venv/bin/python -m pytest -q`.
Tests cover every endpoint, validation, totals, persistence, seeding, cancellation,
and status transitions. Each test uses a temporary SQLite database. A small
ASGI request helper avoids adding an HTTP test-client dependency.

## Structure

- `app/main.py`: application factory and database startup lifecycle
- `app/routes.py`: HTTP routes
- `app/schemas.py`: request validation
- `app/services.py`: order rules and transaction orchestration
- `app/repository.py`: schema, seed data, and SQL persistence
- `tests/test_api.py`: endpoint tests

Tables: `restaurants`, `menu_items`, `orders`, and `order_items`. Order items
store `order_id`, `menu_item_id`, `quantity`, and `unit_price_cents` plus an ID.
No authentication or external services are included.
