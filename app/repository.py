"""SQLite storage. Each connection enforces foreign keys and commits atomically."""
import sqlite3
from contextlib import contextmanager


SCHEMA = """
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, cuisine TEXT NOT NULL,
    opens_at TEXT NOT NULL, closes_at TEXT NOT NULL,
    avg_prep_minutes INTEGER NOT NULL CHECK(avg_prep_minutes > 0)
);
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    name TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents >= 0)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    status TEXT NOT NULL CHECK(status IN
        ('pending', 'preparing', 'out_for_delivery', 'delivered', 'cancelled')),
    total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
    address TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0)
);
"""


class Repository:
    def __init__(self, path):
        self.path = str(path)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as db:
            db.executescript(SCHEMA)
            restaurants = [
                (1, 'Pizza Corner', 'Italian', '11:00', '22:00', 20),
                (2, 'Sushi Garden', 'Japanese', '12:00', '21:00', 25),
                (3, 'Taco Stop', 'Mexican', '10:00', '23:00', 15),
                (4, 'Curry House', 'Indian', '11:00', '22:00', 30),
                (5, 'Green Bowl', 'Vegetarian', '09:00', '20:00', 10),
            ]
            db.executemany('INSERT OR IGNORE INTO restaurants VALUES (?, ?, ?, ?, ?, ?)', restaurants)
            db.executemany('INSERT OR IGNORE INTO menu_items VALUES (?, ?, ?, ?)', [
                (1, 1, 'Margherita Pizza', 1200), (2, 1, 'Garlic Bread', 500),
                (3, 2, 'Avocado Roll', 800), (4, 2, 'Salmon Roll', 1100),
                (5, 3, 'Bean Tacos', 900), (6, 3, 'Chicken Tacos', 1000),
                (7, 4, 'Chana Masala', 1300), (8, 4, 'Naan', 300),
                (9, 5, 'Harvest Bowl', 1100), (10, 5, 'Garden Salad', 700),
            ])

    def restaurants(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM restaurants ORDER BY id')]

    @staticmethod
    def restaurant(db, restaurant_id):
        return db.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,)).fetchone()

    def menu(self, restaurant_id):
        with self.connect() as db:
            if not self.restaurant(db, restaurant_id):
                return None
            return [dict(row) for row in db.execute(
                'SELECT * FROM menu_items WHERE restaurant_id = ? ORDER BY id', (restaurant_id,))]

    @staticmethod
    def menu_item(db, item_id):
        return db.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)).fetchone()

    @staticmethod
    def insert_order(db, restaurant_id, total, address, created_at, items):
        cursor = db.execute(
            'INSERT INTO orders (restaurant_id, status, total_cents, address, created_at) '
            "VALUES (?, 'pending', ?, ?, ?)", (restaurant_id, total, address, created_at))
        order_id = cursor.lastrowid
        db.executemany(
            'INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price_cents) '
            'VALUES (?, ?, ?, ?)', [(order_id, *item) for item in items])
        return order_id

    @staticmethod
    def order(db, order_id):
        row = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result['items'] = [dict(item) for item in db.execute(
            'SELECT menu_item_id, quantity, unit_price_cents FROM order_items '
            'WHERE order_id = ? ORDER BY id', (order_id,))]
        return result

    @staticmethod
    def update_status(db, order_id, status):
        db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
