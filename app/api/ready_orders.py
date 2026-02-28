from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.order import CartItem, ReadyOrder, ReadyOrderItem
from app.models.catalog import ReadyProduct
from app.models.user import User
from app.schemas.order import ReadyOrderOut

router = APIRouter(prefix="/ready-orders", tags=["Заказы готового мерча"])


async def _get_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/", response_model=ReadyOrderOut, summary="Оформить заказ из корзины")
async def create_ready_order(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """
    Оформляет заказ из корзины.
    Требует заполненных данных доставки (delivery_complete = True).
    """
    user = await _get_user(telegram_id, db)

    if not user.delivery_complete:
        raise HTTPException(
            status_code=400,
            detail="Заполните данные доставки в профиле перед оформлением заказа.",
        )

    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.ready_product))
        .where(CartItem.user_id == user.id)
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    total = Decimal("0")
    for item in cart_items:
        product = item.ready_product
        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"Товар id={product.id} недоступен")
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара id={product.id}. "
                       f"Доступно: {product.stock_quantity}, в корзине: {item.quantity}",
            )
        total += product.price * item.quantity

    order = ReadyOrder(
        user_id=user.id,
        total_price=total,
        carrier=user.delivery_carrier,
        delivery_name=user.delivery_name,
        delivery_phone=user.delivery_phone,
        delivery_city=user.delivery_city,
        delivery_address=user.delivery_address,
    )
    db.add(order)
    await db.flush()

    for item in cart_items:
        product = item.ready_product
        db.add(ReadyOrderItem(
            order_id=order.id,
            ready_product_id=product.id,
            quantity=item.quantity,
            price_fixed=product.price,
        ))
        product.stock_quantity -= item.quantity

    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await db.commit()

    result = await db.execute(
        select(ReadyOrder)
        .options(selectinload(ReadyOrder.items))
        .where(ReadyOrder.id == order.id)
    )
    return result.scalar_one()


@router.get("/my", response_model=list[ReadyOrderOut], summary="Мои заказы")
async def get_my_orders(telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await _get_user(telegram_id, db)
    result = await db.execute(
        select(ReadyOrder)
        .options(selectinload(ReadyOrder.items))
        .where(ReadyOrder.user_id == user.id)
        .order_by(ReadyOrder.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=ReadyOrderOut, summary="Детали заказа")
async def get_order(order_id: int, telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await _get_user(telegram_id, db)
    result = await db.execute(
        select(ReadyOrder)
        .options(selectinload(ReadyOrder.items))
        .where(ReadyOrder.id == order_id, ReadyOrder.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order