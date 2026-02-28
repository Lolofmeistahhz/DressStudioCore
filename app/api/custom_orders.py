from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.order import CustomOrder
from app.models.catalog import ProductType, Color, Print, PrintSize
from app.models.user import User
from app.schemas.order import CustomOrderCreate, CustomOrderOut

router = APIRouter(prefix="/custom-orders", tags=["Кастомные заказы"])


async def _get_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


def _calc_recommended_price(
    product_type: ProductType,
    print_size: Optional[PrintSize],
) -> Decimal:
    """base_price изделия + цена размера вышивки."""
    price = product_type.base_price
    if print_size:
        price += print_size.price
    return price


@router.post("/", response_model=CustomOrderOut, summary="Создать кастомный заказ")
async def create_custom_order(
    telegram_id: int,
    data: CustomOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(telegram_id, db)

    if not user.delivery_complete:
        raise HTTPException(
            status_code=400,
            detail="Заполните данные доставки в профиле перед созданием заказа.",
        )

    pt_result = await db.execute(
        select(ProductType).where(ProductType.id == data.product_type_id, ProductType.is_active == True)
    )
    product_type = pt_result.scalar_one_or_none()
    if not product_type:
        raise HTTPException(status_code=404, detail="Тип изделия не найден")

    color_result = await db.execute(select(Color).where(Color.id == data.color_id))
    color = color_result.scalar_one_or_none()
    if not color:
        raise HTTPException(status_code=404, detail="Цвет не найден")

    print_size: Optional[PrintSize] = None
    if data.print_id:
        print_result = await db.execute(
            select(Print).where(Print.id == data.print_id, Print.is_active == True)
        )
        if not print_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Принт не найден")

        ps_result = await db.execute(
            select(PrintSize).where(
                PrintSize.id == data.print_size_id,
                PrintSize.print_id == data.print_id,
            )
        )
        print_size = ps_result.scalar_one_or_none()
        if not print_size:
            raise HTTPException(status_code=404, detail="Размер вышивки не найден")

    recommended_price = _calc_recommended_price(product_type, print_size)

    order = CustomOrder(
        user_id=user.id,
        product_type_id=data.product_type_id,
        color_id=data.color_id,
        size_label=data.size_label,
        print_id=data.print_id,
        print_size_id=data.print_size_id,
        custom_images=data.custom_images,
        comment=data.comment,
        recommended_price=recommended_price,
        final_price=recommended_price,   # админ может изменить
        carrier=user.delivery_carrier,
        delivery_name=user.delivery_name,
        delivery_phone=user.delivery_phone,
        delivery_city=user.delivery_city,
        delivery_address=user.delivery_address,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/my", response_model=list[CustomOrderOut], summary="Мои кастомные заказы")
async def get_my_custom_orders(telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await _get_user(telegram_id, db)
    result = await db.execute(
        select(CustomOrder)
        .where(CustomOrder.user_id == user.id)
        .order_by(CustomOrder.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=CustomOrderOut, summary="Детали кастомного заказа")
async def get_custom_order(
    order_id: int,
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(telegram_id, db)
    result = await db.execute(
        select(CustomOrder).where(
            CustomOrder.id == order_id,
            CustomOrder.user_id == user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order