"""SQLite storage. Each connection enforces foreign keys and commits atomically."""

# Import sqlite3 for use in this module.
import sqlite3

# Import contextmanager from contextlib.
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
        ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED')),
    total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
    address TEXT NOT NULL, created_at TEXT NOT NULL,
    delivery_distance_km REAL NOT NULL CHECK(delivery_distance_km >= 0),
    estimated_delivery_at TEXT, eta_updated_at TEXT
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0)
);
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    status TEXT NOT NULL CHECK(status IN
        ('PLACED', 'PREPARING', 'READY', 'PICKED_UP', 'DELIVERED', 'CANCELLED')),
    changed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS history_by_order ON order_status_history(order_id, id);
"""


# Define the Repository class.
class Repository:

    # Initialize the object with its required collaborators.
    def __init__(self, path):

        # Set self.path to str(path).
        self.path = str(path)

    # Apply this decorator to configure the function defined below.
    @contextmanager
    # Define connect.
    def connect(self):

        # Set connection to sqlite3.connect(self.path).
        connection = sqlite3.connect(self.path)

        # Set connection.row_factory to sqlite3.Row.
        connection.row_factory = sqlite3.Row

        # Call connection.execute('PRAGMA foreign_keys = ON').
        connection.execute('PRAGMA foreign_keys = ON')

        # Attempt these operations and handle the exceptions listed below.
        try:

            # Enter connection and run the indented block with its cleanup
            # behavior.
            with connection:

                # Yield connection to the caller.
                yield connection
        # Run cleanup whether the preceding operations succeed or fail.
        finally:

            # Call connection.close().
            connection.close()

    # Define initialize.
    def initialize(self):

        # Enter self.connect() and run the indented block with its cleanup
        # behavior.
        with self.connect() as db:

            # Set existing to db.execute("SELECT sql FROM sqlite_master WHERE
            # type = 'table' AND name = 'orders'").fetchone().
            existing = db.execute(

                # Supply the remaining arguments or values for the
                # expression above.
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'orders'"

            # Supply the remaining arguments or values for the expression
            # above.
            ).fetchone()

            # Run this branch when existing and "'pending'" in
            # existing['sql'].
            if existing and "'pending'" in existing['sql']:

                # Raise RuntimeError('Legacy order schema requires an
                # approved migration. Use MINIDASH_DB with a new database
                # path for Track C.') to report the failure.
                raise RuntimeError(

                    # Supply the remaining arguments or values for the
                    # expression above.
                    'Legacy order schema requires an approved migration. '

                    # Supply the remaining arguments or values for the
                    # expression above.
                    'Use MINIDASH_DB with a new database path for Track C.'

                # Finish the expression started above.
                )

            # Run this branch when existing and 'delivery_distance_km' not in
            # existing['sql'].
            if existing and 'delivery_distance_km' not in existing['sql']:

                # Raise RuntimeError('Pre-ETA schema requires an approved
                # migration; use a new MINIDASH_DB path.') to report the
                # failure.
                raise RuntimeError('Pre-ETA schema requires an approved migration; use a new MINIDASH_DB path.')

            # Call db.executescript(SCHEMA).
            db.executescript(SCHEMA)

            # Build the value below and store it in restaurants.
            restaurants = [

                # Supply the remaining arguments or values for the
                # expression above.
                (1, 'Pizza Corner', 'Italian', '11:00', '22:00', 20),

                # Supply the remaining arguments or values for the
                # expression above.
                (2, 'Sushi Garden', 'Japanese', '12:00', '21:00', 25),

                # Supply the remaining arguments or values for the
                # expression above.
                (3, 'Taco Stop', 'Mexican', '10:00', '23:00', 15),

                # Supply the remaining arguments or values for the
                # expression above.
                (4, 'Curry House', 'Indian', '11:00', '22:00', 30),

                # Supply the remaining arguments or values for the
                # expression above.
                (5, 'Green Bowl', 'Vegetarian', '09:00', '20:00', 10),

            # Finish the expression started above.
            ]

            # Call db.executemany('INSERT OR IGNORE INTO restaurants VALUES
            # (?, ?, ?, ?, ?, ?)', restaurants).
            db.executemany('INSERT OR IGNORE INTO restaurants VALUES (?, ?, ?, ?, ?, ?)', restaurants)

            # Call db.executemany('INSERT OR IGNORE INTO menu_items VALUES (?,
            # ?, ?, ?)', [(1, 1, 'Margherita Pizza', 1200), (2, 1, 'Garlic
            # Bread', 500), (3, 2, 'Avocado Roll', 800), (4, 2, 'Salmon...
            db.executemany('INSERT OR IGNORE INTO menu_items VALUES (?, ?, ?, ?)', [

                # Supply the remaining arguments or values for the
                # expression above.
                (1, 1, 'Margherita Pizza', 1200), (2, 1, 'Garlic Bread', 500),

                # Supply the remaining arguments or values for the
                # expression above.
                (3, 2, 'Avocado Roll', 800), (4, 2, 'Salmon Roll', 1100),

                # Supply the remaining arguments or values for the
                # expression above.
                (5, 3, 'Bean Tacos', 900), (6, 3, 'Chicken Tacos', 1000),

                # Supply the remaining arguments or values for the
                # expression above.
                (7, 4, 'Chana Masala', 1300), (8, 4, 'Naan', 300),

                # Supply the remaining arguments or values for the
                # expression above.
                (9, 5, 'Harvest Bowl', 1100), (10, 5, 'Garden Salad', 700),

            # Finish the expression started above.
            ])

    # Define restaurants.
    def restaurants(self):

        # Enter self.connect() and run the indented block with its cleanup
        # behavior.
        with self.connect() as db:

            # Return [dict(row) for row in db.execute('SELECT * FROM
            # restaurants ORDER BY id')].
            return [dict(row) for row in db.execute('SELECT * FROM restaurants ORDER BY id')]

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define restaurant.
    def restaurant(db, restaurant_id):

        # Return db.execute('SELECT * FROM restaurants WHERE id = ?',
        # (restaurant_id,)).fetchone().
        return db.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,)).fetchone()

    # Define menu.
    def menu(self, restaurant_id):

        # Enter self.connect() and run the indented block with its cleanup
        # behavior.
        with self.connect() as db:

            # Run this branch when not self.restaurant(db, restaurant_id).
            if not self.restaurant(db, restaurant_id):

                # Return None.
                return None

            # Return [dict(row) for row in db.execute('SELECT * FROM
            # menu_items WHERE restaurant_id = ? ORDER BY id',
            # (restaurant_id,))].
            return [dict(row) for row in db.execute(

                # Supply the remaining arguments or values for the
                # expression above.
                'SELECT * FROM menu_items WHERE restaurant_id = ? ORDER BY id', (restaurant_id,))]

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define menu item.
    def menu_item(db, item_id):

        # Return db.execute('SELECT * FROM menu_items WHERE id = ?',
        # (item_id,)).fetchone().
        return db.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)).fetchone()

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define insert order.
    def insert_order(db, restaurant_id, total, address, created_at, items,

                     # Supply the remaining arguments or values for
                     # the expression above.
                     delivery_distance_km=0):

        # Build the value below and store it in cursor.
        cursor = db.execute(

            # Supply the remaining arguments or values for the expression
            # above.
            'INSERT INTO orders (restaurant_id, status, total_cents, address, created_at, delivery_distance_km) '

            # Supply the remaining arguments or values for the expression
            # above.
            "VALUES (?, 'PLACED', ?, ?, ?, ?)",

            # Supply the remaining arguments or values for the expression
            # above.
            (restaurant_id, total, address, created_at, delivery_distance_km))

        # Set order_id to cursor.lastrowid.
        order_id = cursor.lastrowid

        # Call db.executemany('INSERT INTO order_items (order_id, menu_item_id,
        # quantity, unit_price_cents) VALUES (?, ?, ?, ?)', [(order_id, *item) for
        # item in items]).
        db.executemany(

            # Supply the remaining arguments or values for the expression
            # above.
            'INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price_cents) '

            # Supply the remaining arguments or values for the expression
            # above.
            'VALUES (?, ?, ?, ?)', [(order_id, *item) for item in items])

        # Call Repository.append_status_history(db, order_id, 'PLACED',
        # created_at).
        Repository.append_status_history(db, order_id, 'PLACED', created_at)

        # Return order_id.
        return order_id

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define append status history.
    def append_status_history(db, order_id, status, changed_at):

        # Call db.execute('INSERT INTO order_status_history (order_id, status,
        # changed_at) VALUES (?, ?, ?)', (order_id, status, changed_at)).
        db.execute(

            # Supply the remaining arguments or values for the expression
            # above.
            'INSERT INTO order_status_history (order_id, status, changed_at) VALUES (?, ?, ?)',

            # Supply the remaining arguments or values for the expression
            # above.
            (order_id, status, changed_at))

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define status history.
    def status_history(db, order_id):

        # Return [dict(row) for row in db.execute('SELECT status, changed_at FROM
        # order_status_history WHERE order_id = ? ORDER BY id', (order_id,))].
        return [dict(row) for row in db.execute(

            # Supply the remaining arguments or values for the expression
            # above.
            'SELECT status, changed_at FROM order_status_history WHERE order_id = ? ORDER BY id',

            # Supply the remaining arguments or values for the expression
            # above.
            (order_id,))]

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define order.
    def order(db, order_id):

        # Set row to db.execute('SELECT * FROM orders WHERE id = ?',
        # (order_id,)).fetchone().
        row = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

        # Run this branch when row is None.
        if row is None:

            # Return None.
            return None

        # Set result to dict(row).
        result = dict(row)

        # Build the value below and store it in result['items'].
        result['items'] = [dict(item) for item in db.execute(

            # Supply the remaining arguments or values for the expression
            # above.
            'SELECT menu_item_id, quantity, unit_price_cents FROM order_items '

            # Supply the remaining arguments or values for the expression
            # above.
            'WHERE order_id = ? ORDER BY id', (order_id,))]

        # Return result.
        return result

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define update status.
    def update_status(db, order_id, status):

        # Call db.execute('UPDATE orders SET status = ? WHERE id = ?', (status,
        # order_id)).
        db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))

    # Apply this decorator to configure the function defined below.
    @staticmethod
    # Define update eta.
    def update_eta(db, order_id, estimated_delivery_at, eta_updated_at):

        # Call db.execute('UPDATE orders SET estimated_delivery_at = ?,
        # eta_updated_at = ? WHERE id = ?', (estimated_delivery_at,
        # eta_updated_at, order_id)).
        db.execute('UPDATE orders SET estimated_delivery_at = ?, eta_updated_at = ? WHERE id = ?',

                   # Supply the remaining arguments or values for the
                   # expression above.
                   (estimated_delivery_at, eta_updated_at, order_id))
