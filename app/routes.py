# Import APIRouter, HTTPException, Request from fastapi.
from fastapi import APIRouter, HTTPException, Request

# Import OrderInput, StatusInput from .schemas.
from .schemas import OrderInput, StatusInput

# Import OrderService from .services.
from .services import OrderService

# Set router to APIRouter().
router = APIRouter()


# Apply this decorator to configure the function defined below.
@router.get('/restaurants')
# Define restaurants.
def restaurants(request: Request):

    # Return request.app.state.repository.restaurants().
    return request.app.state.repository.restaurants()


# Apply this decorator to configure the function defined below.
@router.get('/restaurants/{id}/menu')
# Define menu.
def menu(id: int, request: Request):

    # Set result to request.app.state.repository.menu(id).
    result = request.app.state.repository.menu(id)

    # Run this branch when result is None.
    if result is None:

        # Raise HTTPException(404, 'Restaurant not found') to report the failure.
        raise HTTPException(404, 'Restaurant not found')

    # Return result.
    return result


# Apply this decorator to configure the function defined below.
@router.post('/orders', status_code=201)
# Define create order.
def create_order(payload: OrderInput, request: Request):

    # Return OrderService(request.app.state.repository).create(payload).
    return OrderService(request.app.state.repository).create(payload)


# Apply this decorator to configure the function defined below.
@router.get('/orders/{id}')
# Define get order.
def get_order(id: int, request: Request):

    # Return OrderService(request.app.state.repository).get(id).
    return OrderService(request.app.state.repository).get(id)


# Apply this decorator to configure the function defined below.
@router.patch('/orders/{id}/status')
# Define update status.
def update_status(id: int, payload: StatusInput, request: Request):

    # Return OrderService(request.app.state.repository).change_status(id,
    # payload.status).
    return OrderService(request.app.state.repository).change_status(id, payload.status)


# Apply this decorator to configure the function defined below.
@router.get('/orders/{id}/tracking')
# Define tracking.
def tracking(id: int, request: Request):

    # Return OrderService(request.app.state.repository).tracking(id).
    return OrderService(request.app.state.repository).tracking(id)
