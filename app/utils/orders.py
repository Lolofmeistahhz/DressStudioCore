from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReadyOrder, CustomOrder, User


async def get_ready_order_by_id(db: AsyncSession, order_id: int) -> ReadyOrder | None:
    """Получить готовый заказ по ID."""
    result = await db.execute(
        select(ReadyOrder).where(ReadyOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_custom_order_by_id(db: AsyncSession, order_id: int) -> CustomOrder | None:
    """Получить кастомный заказ по ID."""
    result = await db.execute(
        select(CustomOrder).where(CustomOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Получить пользователя по ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()