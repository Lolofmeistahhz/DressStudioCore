from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserUpsert, DeliveryUpdate, PhoneUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Пользователи"])


async def get_user_by_tg(telegram_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/me", response_model=UserOut, summary="Создать или обновить пользователя")
async def upsert_user(data: UserUpsert, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=data.telegram_id,
            username=data.username,
            full_name=data.full_name,
        )
        db.add(user)
    else:
        if data.username:
            user.username = data.username
        if data.full_name:
            user.full_name = data.full_name

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserOut, summary="Получить профиль")
async def get_me(telegram_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_by_tg(telegram_id, db)


@router.patch("/me/delivery", response_model=UserOut, summary="Обновить данные доставки")
async def update_delivery(
    telegram_id: int,
    data: DeliveryUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_tg(telegram_id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/me/phone", response_model=UserOut, summary="Сохранить телефон")
async def update_phone(
    telegram_id: int,
    data: PhoneUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_tg(telegram_id, db)
    user.phone = data.phone
    await db.commit()
    await db.refresh(user)
    return user