"""SQLite persistence checks independent of FastAPI installation."""
import sqlite3

import pytest

from app.repository import Repository

def test_history_preserves_event_order_when_timestamps_tie(tmp_path):
    repo = Repository(tmp_path / 'ties.db')
    repo.initialize()
    with repo.connect() as db:
        order_id = repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])
        repo.update_status(db, order_id, 'PREPARING')
        repo.append_status_history(db, order_id, 'PREPARING', '2026-10-30T12:00:00+00:00')
        assert [row['status'] for row in repo.status_history(db, order_id)] == ['PLACED', 'PREPARING']


def test_legacy_schema_is_rejected_without_changes(tmp_path):
    path = tmp_path / 'legacy.db'
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT CHECK(status IN ('pending', 'delivered')))")
        db.execute("INSERT INTO orders VALUES (1, 'pending')")
    with pytest.raises(RuntimeError, match='approved migration'):
        Repository(path).initialize()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT * FROM orders').fetchall() == [(1, 'pending')]
        assert db.execute("SELECT name FROM sqlite_master WHERE name = 'order_status_history'").fetchall() == []


def test_history_persists_across_repository_restarts(tmp_path):
    path = tmp_path / 'restart.db'
    repo = Repository(path)
    repo.initialize()
    with repo.connect() as db:
        order_id = repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])
        repo.update_status(db, order_id, 'PREPARING')
        repo.append_status_history(db, order_id, 'PREPARING', '2026-10-30T12:01:00+00:00')
        expected = repo.status_history(db, order_id)
    restarted = Repository(path)
    restarted.initialize()
    restarted.initialize()
    with restarted.connect() as db:
        assert restarted.order(db, order_id)['status'] == 'PREPARING'
        assert restarted.status_history(db, order_id) == expected
        assert expected == [
            {'status': 'PLACED', 'changed_at': '2026-10-30T12:00:00+00:00'},
            {'status': 'PREPARING', 'changed_at': '2026-10-30T12:01:00+00:00'},
        ]


def test_transaction_rolls_back_status_and_history(tmp_path):
    repo = Repository(tmp_path / 'rollback.db')
    repo.initialize()
    with repo.connect() as db:
        repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)])
    with pytest.raises(sqlite3.IntegrityError):
        with repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            repo.update_status(db, 1, 'PREPARING')
            repo.append_status_history(db, 1, 'PREPARING', None)
    with repo.connect() as db:
        assert repo.order(db, 1)['status'] == 'PLACED'
        assert [row['status'] for row in repo.status_history(db, 1)] == ['PLACED']


def test_eta_persistence_and_restart(tmp_path):
    path = tmp_path / 'eta.db'
    repo = Repository(path)
    repo.initialize()
    with repo.connect() as db:
        repo.insert_order(db, 1, 1200, 'Address', '2026-10-30T12:00:00+00:00', [(1, 1, 1200)], 6)
        repo.update_eta(db, 1, '2026-10-30T12:32:00+00:00', '2026-10-30T12:00:00+00:00')
    restarted = Repository(path)
    restarted.initialize()
    with restarted.connect() as db:
        order = restarted.order(db, 1)
        assert order['delivery_distance_km'] == 6
        assert order['estimated_delivery_at'] == '2026-10-30T12:32:00+00:00'
        assert order['eta_updated_at'] == '2026-10-30T12:00:00+00:00'
