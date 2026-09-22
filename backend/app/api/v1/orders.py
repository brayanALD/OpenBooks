from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.deps import get_current_user, get_order_service
from app.domain.models import Order, User
from app.schemas.orders import (
    CheckoutIn,
    OrderItemOut,
    OrderOut,
    PaymentOut,
    ShippingOut,
)
from app.services.order_service import CheckoutError, OrderService

router = APIRouter(prefix="/orders", tags=["pedidos"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Orders = Annotated[OrderService, Depends(get_order_service)]

# Códigos de negocio -> HTTP. 409 = el carrito o los precios ya no coinciden con lo que vio el usuario.
_CHECKOUT_STATUS = {"empty_cart": 422, "cart_issues": 409, "total_changed": 409}


def to_order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        number=order.number,
        status=order.status,
        items=[OrderItemOut(**item.model_dump()) for item in order.items],
        subtotal_cop=order.subtotal_cop,
        shipping_cop=order.shipping_cop,
        total_cop=order.total_cop,
        shipping=ShippingOut(**order.shipping.model_dump()),
        payment=PaymentOut(
            status=order.payment.status,
            method=order.payment.method,
            reference=order.payment.reference,
            failure_reason=order.payment.failure_reason,
        ),
        created_at=order.created_at,
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(body: CheckoutIn, user: CurrentUser, orders: Orders, response: Response) -> OrderOut:
    """Crea el pedido y cobra. Un pago rechazado NO es un error HTTP: devuelve el pedido con `status: "failed"`.

    Si la `idempotency_key` ya existía se devuelve el pedido original con 200 en vez de 201 (no se cobra otra vez).
    """
    try:
        order, created = orders.checkout(user, body)
    except CheckoutError as error:
        raise HTTPException(
            _CHECKOUT_STATUS.get(error.code, 409), {"code": error.code, "message": error.message}
        ) from None
    if not created:
        response.status_code = status.HTTP_200_OK
    return to_order_out(order)


@router.get("", response_model=list[OrderOut])
def my_orders(user: CurrentUser, orders: Orders) -> list[OrderOut]:
    return [to_order_out(o) for o in orders.list_for_user(user.id)]


@router.get("/{order_id}", response_model=OrderOut)
def my_order(order_id: str, user: CurrentUser, orders: Orders) -> OrderOut:
    order = orders.get_for_user(order_id, user.id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return to_order_out(order)
