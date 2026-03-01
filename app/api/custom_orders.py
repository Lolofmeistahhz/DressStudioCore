"""
app/api/custom_orders.py

Фикс: custom_images теперь явно сохраняется в модель.
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
    custom_images: Optional[list[str]] = None   # список URL загруженных фото
    comment:       Optional[str]       = None


@router.post("/")
async def create_custom_order(
    body: CustomOrderCreate,
    telegram_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # Получаем пользователя
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if not user.delivery_complete:
        raise HTTPException(400, "Delivery info incomplete")

    # Рассчитываем рекомендованную цену
    recommended_price: Decimal | None = None
    if body.print_size_id:
        ps_result = await db.execute(select(PrintSize).where(PrintSize.id == body.print_size_id))
        ps = ps_result.scalar_one_or_none()
        if ps:
            recommended_price = ps.price

    order = CustomOrder(
        user_id         = user.id,
        product_type_id = body.product_type_id,
        color_id        = body.color_id,
        size_label      = body.size_label,
        print_id        = body.print_id,
        print_size_id   = body.print_size_id,
        custom_images   = body.custom_images,  # ← явно сохраняем список URL
        comment         = body.comment,
        recommended_price = recommended_price,
        # Снапшот доставки
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
        "custom_images": order.custom_images,   # возвращаем обратно для подтверждения
    }


@router.get("/my")
async def my_custom_orders(telegram_id: int = Query(...), db: AsyncSession = Depends(get_db)):
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
            "custom_images": o.custom_images,
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]