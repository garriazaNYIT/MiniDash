from fastapi import APIRouter, HTTPException, Request

from .schemas import OrderInput, StatusInput
from .services import OrderService

router = APIRouter()


@router.get('/restaurants')
def restaurants(request: Request):
    return request.app.state.repository.restaurants()


@router.get('/restaurants/{id}/menu')
def menu(id: int, request: Request):
    result = request.app.state.repository.menu(id)
    if result is None:
        raise HTTPException(404, 'Restaurant not found')
    return result


@router.post('/orders', status_code=201)
def create_order(payload: OrderInput, request: Request):
    return OrderService(request.app.state.repository).create(payload)


@router.get('/orders/{id}')
def get_order(id: int, request: Request):
    return OrderService(request.app.state.repository).get(id)


@router.patch('/orders/{id}/status')
def update_status(id: int, payload: StatusInput, request: Request):
    return OrderService(request.app.state.repository).change_status(id, payload.status)


@router.get('/orders/{id}/tracking')
def tracking(id: int, request: Request):
    return OrderService(request.app.state.repository).tracking(id)
