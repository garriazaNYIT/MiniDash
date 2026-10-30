"""Business rules and atomic order operations."""
from datetime import datetime, timezone

from fastapi import HTTPException

from .order_tracking import is_status_change

class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, payload):
        address = payload.address.strip()
        if not address:
            raise HTTPException(422, 'Address must not be blank')
        repo = self.repository
        with repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not repo.restaurant(db, payload.restaurant_id):
                raise HTTPException(404, 'Restaurant not found')
            items = []
            seen = set()
            for requested in payload.items:
                if requested.menu_item_id in seen:
                    raise HTTPException(422, 'Duplicate menu item; use quantity instead')
                seen.add(requested.menu_item_id)
                item = repo.menu_item(db, requested.menu_item_id)
                if item is None or item['restaurant_id'] != payload.restaurant_id:
                    raise HTTPException(422, 'Menu item does not belong to this restaurant')
                items.append((item['id'], requested.quantity, item['price_cents']))
            total = sum(quantity * price for _, quantity, price in items)
            if total > 9223372036854775807:
                raise HTTPException(422, 'Order total exceeds supported range')
            order_id = repo.insert_order(db, payload.restaurant_id, total, address,
                                         datetime.now(timezone.utc).isoformat(), items)
            return repo.order(db, order_id)

    def get(self, order_id):
        with self.repository.connect() as db:
            order = self.repository.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            return order

    def tracking(self, order_id):
        repo = self.repository
        with repo.connect() as db:
            # Keep the order and history reads in the same SQLite snapshot.
            db.execute('BEGIN')
            order = repo.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            return {
                'order_id': order['id'],
                'status': order['status'],
                'history': repo.status_history(db, order_id),
            }

    def change_status(self, order_id, status):
        repo = self.repository
        with repo.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            order = repo.order(db, order_id)
            if order is None:
                raise HTTPException(404, 'Order not found')
            try:
                changed = is_status_change(order['status'], status)
            except ValueError:
                raise HTTPException(409, 'Invalid status transition') from None
            if not changed:
                return order
            repo.update_status(db, order_id, status)
            repo.append_status_history(db, order_id, status,
                                       datetime.now(timezone.utc).isoformat())
            return repo.order(db, order_id)
