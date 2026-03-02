import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.payment import Payment, PaymentEntityType, PaymentStatus
from app.models.order import ReadyOrder, ReadyOrderStatus, CustomOrder, CustomOrderStatus
from app.schemas.payment import PaymentCreate, PaymentInitResponse, PaymentOut
from app.utils.shared import create_payment_for_order
from app.utils.orders import get_ready_order_by_id, get_custom_order_by_id, get_user_by_id
from app.utils.notifications import send_telegram_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Оплата"])


async def _notify_telegram(telegram_id: int, text: str) -> None:
    """Отправка уведомления в Telegram."""
    await send_telegram_message(telegram_id, text)


# ── 1. Создание платежа ───────────────────────────────────────────────────────

@router.post("/create", response_model=PaymentInitResponse, summary="Создать платёж")
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    """Создает платеж через ЮKassa."""
    return await create_payment_for_order(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        amount=data.amount,
        db=db
    )


# ── 2. Вебхук ────────────────────────────────────────────────────────────────

@router.post("/webhook", summary="Вебхук ЮKassa")
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Обработка вебхука от ЮKassa."""
    event = await request.json()
    event_type = event.get("event")
    yk_payment_id = event.get("object", {}).get("id")

    logger.info(f"Webhook: event={event_type}, yk_id={yk_payment_id}")

    result = await db.execute(select(Payment).where(Payment.yookassa_payment_id == yk_payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        logger.warning(f"Payment {yk_payment_id} not found")
        return {"status": "not_found"}

    if event_type == "payment.succeeded":
        await _handle_succeeded(payment, db)
    elif event_type == "payment.canceled":
        payment.status = PaymentStatus.cancelled
        await db.commit()

    return {"status": "ok"}


async def _handle_succeeded(payment: Payment, db) -> None:
    """Обработка успешного платежа."""
    payment.status = PaymentStatus.succeeded
    await db.flush()

    telegram_id = None
    message = ""

    if payment.entity_type == PaymentEntityType.ready_order:
        order = await get_ready_order_by_id(db, payment.entity_id)
        if order:
            order.status = ReadyOrderStatus.paid
            user = await get_user_by_id(db, order.user_id)
            if user:
                telegram_id = user.telegram_id
                message = (
                    f"✅ <b>Оплата прошла!</b>\n\n"
                    f"Заказ <b>№{order.id}</b> оплачен — {payment.amount} ₽\n"
                    f"Приступаем к сборке 📦"
                )

    elif payment.entity_type == PaymentEntityType.custom_order:
        order = await get_custom_order_by_id(db, payment.entity_id)
        if order:
            order.status = CustomOrderStatus.paid
            user = await get_user_by_id(db, order.user_id)
            if user:
                telegram_id = user.telegram_id
                message = (
                    f"✅ <b>Оплата прошла!</b>\n\n"
                    f"Кастомный заказ <b>№{order.id}</b> оплачен — {payment.amount} ₽\n"
                    f"Приступаем к работе 🧵"
                )

    await db.commit()
    if telegram_id and message:
        await _notify_telegram(telegram_id, message)


# ── 3. После редиректа ────────────────────────────────────────────────────────

@router.get("/success", summary="После оплаты")
async def payment_success():
    return {"message": "Оплата завершена. Вернитесь в бот."}


# ── 4. Статус — ПОСЛЕДНИМ (жадный маршрут) ───────────────────────────────────

@router.get("/{payment_id}", response_model=PaymentOut, summary="Статус платежа")
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    return payment