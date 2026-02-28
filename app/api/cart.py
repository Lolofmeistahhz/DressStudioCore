from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.order import CartItem
from app.models.catalog import ReadyProduct
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartOut, CartItemOut

router = APIRouter(prefix="/cart", tags=["Корзина"])


async def _get_user(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


async def _load_cart_items(user_id: int, db: AsyncSession) -> list[CartItem]:
    result = await db.execute(
        select(CartItem)
        .options(
            selectinload(CartItem.ready_product).selectinload(ReadyProduct.product_type),
            selectinload(CartItem.ready_product).selectinload(ReadyProduct.color),
        )
        .where(CartItem.user_id == user_id)
    )
    return result.scalars().all()


def _build_cart_out(items: list[CartItem]) -> CartOut:
    out_items = []
    total = Decimal("0")
    for item in items:
        subtotal = item.ready_product.price * item.quantity
        total += subtotal
        out_items.append(CartItemOut(
            id=item.id,
            ready_product=item.ready_product,
            quantity=item.quantity,
            subtotal=subtotal,
        ))
    return CartOut(
        items=out_items,
        total=total,
        items_count=sum(i.quantity for i in items),
    )


@router.get("/", response_model=CartOut, summary="Просмотр корзины")
async def get_cart(telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await _get_user(telegram_id, db)
    items = await _load_cart_items(user.id, db)
    return _build_cart_out(items)


@router.post("/", response_model=CartOut, summary="Добавить товар в корзину")
async def add_to_cart(
    telegram_id: int,
    data: CartItemAdd,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(telegram_id, db)

    result = await db.execute(
        select(ReadyProduct).where(
            ReadyProduct.id == data.ready_product_id,
            ReadyProduct.is_active == True,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    if product.stock_quantity < data.quantity:
        raise HTTPException(status_code=400, detail=f"На складе: {product.stock_quantity} шт.")

    existing = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user.id,
            CartItem.ready_product_id == data.ready_product_id,
        )
    )
    cart_item = existing.scalar_one_or_none()

    if cart_item:
        new_qty = cart_item.quantity + data.quantity
        if product.stock_quantity < new_qty:
            raise HTTPException(
                status_code=400,
                detail=f"В корзине уже {cart_item.quantity} шт. На складе: {product.stock_quantity}",
            )
        cart_item.quantity = new_qty
    else:
        cart_item = CartItem(
            user_id=user.id,
            ready_product_id=data.ready_product_id,
            quantity=data.quantity,
        )
        db.add(cart_item)

    await db.commit()
    items = await _load_cart_items(user.id, db)
    return _build_cart_out(items)


@router.patch("/{item_id}", response_model=CartOut, summary="Изменить количество")
async def update_cart_item(
    item_id: int,
    telegram_id: int,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(telegram_id, db)

    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    if data.quantity <= 0:
        await db.delete(item)
    else:
        prod = await db.execute(select(ReadyProduct).where(ReadyProduct.id == item.ready_product_id))
        product = prod.scalar_one_or_none()
        if product and product.stock_quantity < data.quantity:
            raise HTTPException(status_code=400, detail=f"На складе только {product.stock_quantity} шт.")
        item.quantity = data.quantity

    await db.commit()
    items = await _load_cart_items(user.id, db)
    return _build_cart_out(items)


@router.delete("/{item_id}", response_model=CartOut, summary="Удалить позицию")
async def remove_from_cart(
    item_id: int,
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(telegram_id, db)
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    await db.delete(item)
    await db.commit()
    items = await _load_cart_items(user.id, db)
    return _build_cart_out(items)


@router.delete("/", response_model=CartOut, summary="Очистить корзину")
async def clear_cart(telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await _get_user(telegram_id, db)
    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await db.commit()
    return CartOut(items=[], total=Decimal("0"), items_count=0)