# Order tracking client

From the project root:

```sh
python scripts/poll_tracking.py 1
python scripts/poll_tracking.py 1 --base-url http://localhost:8000
```

The client uses Python's standard library and requires no running API for its mocked tests. It sends GET requests only, displays status, ETA, and remaining minutes when the returned tracking snapshot changes, and waits two seconds between completed attempts. Each request has a ten-second timeout. Connection failures and HTTP 5xx responses are reported and retried until recovery or Ctrl+C; other HTTP errors, including a missing order (404), stop with a message and exit code 1. Delivery, cancellation, and Ctrl+C stop with exit code 0.

## Two-terminal driver demo

With the API running and an existing PLACED order (replace `1` with its ID), run in terminal one:

```sh
python scripts/poll_tracking.py 1
```

Then run in terminal two:

```sh
python scripts/simulate_driver.py 1 --delay 3
```

Both commands accept `--base-url`. The simulation waits three seconds by default before each transition, checks current status via GET, and submits PREPARING, READY, PICKED_UP, then DELIVERED via PATCH. It requires a PLACED starting state and stops if another client changes the expected state, a response is invalid, or any request fails. Requests time out after ten seconds; failed PATCH requests are never retried because their outcome may be uncertain. The server remains responsible for validating transitions if a concurrent update occurs between GET and PATCH. The script creates no orders and never accesses SQLite directly. Ctrl+C stops it.
