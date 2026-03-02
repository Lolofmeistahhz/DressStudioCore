"""
app/api/custom_orders.py

При смене статуса на accepted + final_price:
  - создаём платёж через YooKassa
  - отправляем клиенту ссылку на оплату через бота
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from app.core.database import get_db
from app.models.order import CustomOrder, CustomOrderStatus
from app.models.catalog import PrintSize
from app.models.user import User

router = APIRouter(prefix="/custom-orders", tags=["custom-orders"])


class CustomOrderCreate(BaseModel):
    product_type_id: int
    color_id: int
    size_label: str
    print_id:      Optional[int]       = None
    print_size_id: Optional[int]       = None
    custom_images: Optional[list[str]] = None
    comment:       Optional[str]       = None


class CustomOrderStatusUpdate(BaseModel):
    status:          Optional[str]     = None
    final_price:     Optional[Decimal] = None
    admin_comment:   Optional[str]     = None
    tracking_number: Optional[str]     = None


@router.post("/")
async def create_custom_order(
    body: CustomOrderCreate,
    telegram_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if not user.delivery_complete:
        raise HTTPException(400, "Delivery info incomplete")

    recommended_price: Decimal | None = None
    if body.print_size_id:
        ps_res = await db.execute(select(PrintSize).where(PrintSize.id == body.print_size_id))
        ps = ps_res.scalar_one_or_none()
        if ps:
            recommended_price = ps.price

    order = CustomOrder(
        user_id          = user.id,
        product_type_id  = body.product_type_id,
        color_id         = body.color_id,
        size_label       = body.size_label,
        print_id         = body.print_id,
        print_size_id    = body.print_size_id,
        custom_images    = body.custom_images,
        comment          = body.comment,
        recommended_price= recommended_price,
        carrier          = user.delivery_carrier,
        delivery_name    = user.delivery_name,
        delivery_phone   = user.phone,
        delivery_city    = user.delivery_city,
        delivery_address = user.delivery_address,
        status           = CustomOrderStatus.new,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {
        "id": order.id,
        "status": order.status,
        "recommended_price": str(order.recommended_price) if order.recommended_price else None,
        "custom_images": order.custom_images,
    }


@router.patch("/{order_id}")
async def update_custom_order(
    order_id: int,
    body: CustomOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Эндпоинт для обновления кастомного заказа из AdminAPI / вебхуков.
    При status=accepted + final_price → создаём платёж и шлём клиенту ссылку.
    """
    result = await db.execute(
        select(CustomOrder)
        .where(CustomOrder.id == order_id)
        .options(
            selectinload(CustomOrder.user),
            selectinload(CustomOrder.product_type),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")

    old_status = order.status

    if body.status:
        order.status = CustomOrderStatus(body.status)
    if body.final_price is not None:
        order.final_price = body.final_price
    if body.admin_comment is not None:
        order.admin_comment = body.admin_comment
    if body.tracking_number is not None:
        order.tracking_number = body.tracking_number

    await db.commit()
    await db.refresh(order)

    # Если статус сменился на accepted — создаём платёж и шлём клиенту
    if old_status != CustomOrderStatus.accepted and order.status == CustomOrderStatus.accepted:
        payment_url = await _create_payment_for_custom(order)
        from app.services.notifications import notify_client_custom_order_accepted
        await notify_client_custom_order_accepted(order, payment_url=payment_url)

    return {"id": order.id, "status": order.status}


async def _create_payment_for_custom(order: CustomOrder) -> str | None:
    """Создаём платёж через внутренний payments endpoint."""
    if not order.final_price:
        return None
    try:
        from app.services.payment_service import create_yookassa_payment
        result = await create_yookassa_payment(
            entity_type="custom_order",
            entity_id=order.id,
            amount=float(order.final_price),
        )
        return result.get("confirmation_url") if result else None
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Payment creation error for custom order {order.id}: {e}")
        return None


@router.get("/my")
async def my_custom_orders(
    telegram_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    orders_result = await db.execute(
        select(CustomOrder)
        .where(CustomOrder.user_id == user.id)
        .order_by(CustomOrder.created_at.desc())
        .options(
            selectinload(CustomOrder.product_type),
            selectinload(CustomOrder.color),
        )
    )
    orders = orders_result.scalars().all()
    return [
        {
            "id": o.id,
            "status": o.status,
            "product_type": o.product_type.name,
            "color": o.color.name,
            "size_label": o.size_label,
            "recommended_price": str(o.recommended_price) if o.recommended_price else None,
            "final_price": str(o.final_price) if o.final_price else None,
            "tracking_number": o.tracking_number,
            "custom_images": o.custom_images,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]