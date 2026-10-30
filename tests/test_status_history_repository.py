"""SQLite persistence checks independent of FastAPI installation."""

# Import sqlite3 for use in this module.
import sqlite3

# Import pytest for use in this module.
import pytest

# Import Repository from app.repository.
from app.repository import Repository

# Define the test for history preserves event order when timestamps tie.
def test_history_preserves_event_order_when_timestamps_tie(tmp_path):

    # Set repo to Repository(tmp_path / 'ties.db').
    repo = Repository(tmp_path / 'ties.db')

    # Call repo.initialize().
    repo.initialize()

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Set order_id to repo.insert_order(db, 1, 1200, 'Address',
        # '2026-10-30T12:00:00+00:00', [(1, 1, 1200)]).
        order_id = repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])

        # Call repo.update_status(db, order_id, 'PREPARING').
        repo.update_status(db, order_id, 'PREPARING')

        # Call repo.append_status_history(db, order_id, 'PREPARING',
        # '2026-10-30T12:00:00+00:00').
        repo.append_status_history(db, order_id, 'PREPARING', '2026-10-30T12:00:00+00:00')

        # Verify that [row['status'] for row in repo.status_history(db, order_id)]
        # == ['PLACED', 'PREPARING'].
        assert [row['status'] for row in repo.status_history(db, order_id)] == ['PLACED', 'PREPARING']


# Define the test for legacy schema is rejected without changes.
def test_legacy_schema_is_rejected_without_changes(tmp_path):

    # Set path to tmp_path / 'legacy.db'.
    path = tmp_path / 'legacy.db'

    # Enter sqlite3.connect(path) and run the indented block with its cleanup
    # behavior.
    with sqlite3.connect(path) as db:

        # Call db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status
        # TEXT CHECK(status IN ('pending', 'delivered')))").
        db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT CHECK(status IN ('pending', 'delivered')))")

        # Call db.execute("INSERT INTO orders VALUES (1, 'pending')").
        db.execute("INSERT INTO orders VALUES (1, 'pending')")

    # Enter pytest.raises(RuntimeError, match='approved migration') and run the
    # indented block with its cleanup behavior.
    with pytest.raises(RuntimeError, match='approved migration'):

        # Call Repository(path).initialize().
        Repository(path).initialize()

    # Enter sqlite3.connect(path) and run the indented block with its cleanup
    # behavior.
    with sqlite3.connect(path) as db:

        # Verify that db.execute('SELECT * FROM orders').fetchall() == [(1,
        # 'pending')].
        assert db.execute('SELECT * FROM orders').fetchall() == [(1, 'pending')]

        # Verify that db.execute("SELECT name FROM sqlite_master WHERE name =
        # 'order_status_history'").fetchall() == [].
        assert db.execute("SELECT name FROM sqlite_master WHERE name = 'order_status_history'").fetchall() == []


# Define the test for history persists across repository restarts.
def test_history_persists_across_repository_restarts(tmp_path):

    # Set path to tmp_path / 'restart.db'.
    path = tmp_path / 'restart.db'

    # Set repo to Repository(path).
    repo = Repository(path)

    # Call repo.initialize().
    repo.initialize()

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Set order_id to repo.insert_order(db, 1, 1200, 'Address',
        # '2026-10-30T12:00:00+00:00', [(1, 1, 1200)]).
        order_id = repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])

        # Call repo.update_status(db, order_id, 'PREPARING').
        repo.update_status(db, order_id, 'PREPARING')

        # Call repo.append_status_history(db, order_id, 'PREPARING',
        # '2026-10-30T12:01:00+00:00').
        repo.append_status_history(db, order_id, 'PREPARING', '2026-10-30T12:01:00+00:00')

        # Set expected to repo.status_history(db, order_id).
        expected = repo.status_history(db, order_id)

    # Set restarted to Repository(path).
    restarted = Repository(path)

    # Call restarted.initialize().
    restarted.initialize()

    # Call restarted.initialize().
    restarted.initialize()

    # Enter restarted.connect() and run the indented block with its cleanup behavior.
    with restarted.connect() as db:

        # Verify that restarted.order(db, order_id)['status'] == 'PREPARING'.
        assert restarted.order(db, order_id)['status'] == 'PREPARING'

        # Verify that restarted.status_history(db, order_id) == expected.
        assert restarted.status_history(db, order_id) == expected

        # Verify that expected == [{'status': 'PLACED', 'changed_at':
        # '2026-10-30T12:00:00+00:00'}, {'status': 'PREPARING', 'changed_at':
        # '2026-10-30T12:01:00+00:00'}].
        assert expected == [

            # Supply the remaining arguments or values for the expression
            # above.
            {'status': 'PLACED', 'changed_at': '2026-10-30T12:00:00+00:00'},

            # Supply the remaining arguments or values for the expression
            # above.
            {'status': 'PREPARING', 'changed_at': '2026-10-30T12:01:00+00:00'},

        # Finish the expression started above.
        ]


# Define the test for transaction rolls back status and history.
def test_transaction_rolls_back_status_and_history(tmp_path):

    # Set repo to Repository(tmp_path / 'rollback.db').
    repo = Repository(tmp_path / 'rollback.db')

    # Call repo.initialize().
    repo.initialize()

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Call repo.insert_order(db, 1, 1200, 'Address',
        # '2026-10-30T12:00:00+00:00', [(1, 1, 1200)]).
        repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])

    # Enter pytest.raises(sqlite3.IntegrityError) and run the indented block with its
    # cleanup behavior.
    with pytest.raises(sqlite3.IntegrityError):

        # Enter repo.connect() and run the indented block with its cleanup
        # behavior.
        with repo.connect() as db:

            # Call db.execute('BEGIN IMMEDIATE').
            db.execute('BEGIN IMMEDIATE')

            # Call repo.update_status(db, 1, 'PREPARING').
            repo.update_status(db, 1, 'PREPARING')

            # Call repo.append_status_history(db, 1, 'PREPARING', None).
            repo.append_status_history(db, 1, 'PREPARING', None)

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Verify that repo.order(db, 1)['status'] == 'PLACED'.
        assert repo.order(db, 1)['status'] == 'PLACED'

        # Verify that [row['status'] for row in repo.status_history(db, 1)] ==
        # ['PLACED'].
        assert [row['status'] for row in repo.status_history(db, 1)] == ['PLACED']


# Define the test for eta persistence and restart.
def test_eta_persistence_and_restart(tmp_path):

    # Set path to tmp_path / 'eta.db'.
    path = tmp_path / 'eta.db'

    # Set repo to Repository(path).
    repo = Repository(path)

    # Call repo.initialize().
    repo.initialize()

    # Enter repo.connect() and run the indented block with its cleanup behavior.
    with repo.connect() as db:

        # Call repo.insert_order(db, 1, 1200, 'Address',
        # '2026-10-30T12:00:00+00:00', [(1, 1, 1200)], 6).
        repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)], 6)

        # Call repo.update_eta(db, 1, '2026-10-30T12:32:00+00:00',
        # '2026-10-30T12:00:00+00:00').
        repo.update_eta(db, 1, '2026-10-30T12:32:00+00:00', '2026-10-30T12:00:00+00:00')

    # Set restarted to Repository(path).
    restarted = Repository(path)

    # Call restarted.initialize().
    restarted.initialize()

    # Enter restarted.connect() and run the indented block with its cleanup behavior.
    with restarted.connect() as db:

        # Set order to restarted.order(db, 1).
        order = restarted.order(db, 1)

        # Verify that order['delivery_distance_km'] == 6.
        assert order['delivery_distance_km'] == 6

        # Verify that order['estimated_delivery_at'] ==
        # '2026-10-30T12:32:00+00:00'.
        assert order['estimated_delivery_at'] == '2026-10-30T12:32:00+00:00'

        # Verify that order['eta_updated_at'] == '2026-10-30T12:00:00+00:00'.
        assert order['eta_updated_at'] == '2026-10-30T12:00:00+00:00'
