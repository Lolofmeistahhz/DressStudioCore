import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.order import ReadyOrder, ReadyOrderStatus, CustomOrder, CustomOrderStatus
from app.models.payment import Payment, PaymentEntityType, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentInitResponse, PaymentOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Оплата"])


def _yookassa():
    try:
        from yookassa import Configuration, Payment as YKPayment
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        return YKPayment
    except ImportError:
        raise HTTPException(status_code=503, detail="pip install yookassa")


async def _notify_telegram(telegram_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json={"chat_id": telegram_id, "text": text, "parse_mode": "HTML"})
    except Exception as e:
        logger.warning(f"Telegram notify error: {e}")


# ── 1. Создание платежа ───────────────────────────────────────────────────────

@router.post("/create", response_model=PaymentInitResponse, summary="Создать платёж")
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    YKPayment = _yookassa()

    descriptions = {
        PaymentEntityType.ready_order:       f"Заказ готового мерча №{data.entity_id}",
        PaymentEntityType.custom_order:      f"Кастомный заказ №{data.entity_id}",
        PaymentEntityType.constructor_order: f"Заказ из конструктора №{data.entity_id}",
    }

    webhook_base = settings.WEBHOOK_URL.rstrip("/")
    yk_payment = YKPayment.create({
        "amount": {"value": f"{data.amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": f"{webhook_base}/api/v1/payments/success",
        },
        "capture": True,
        "description": descriptions[data.entity_type],
        "metadata": {
            "entity_type": data.entity_type.value,
            "entity_id": str(data.entity_id),
        },
    })

    payment = Payment(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        amount=data.amount,
        yookassa_payment_id=yk_payment.id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentInitResponse(
        payment_id=payment.id,
        yookassa_payment_id=yk_payment.id,
        confirmation_url=yk_payment.confirmation.confirmation_url,
        amount=data.amount,
    )


# ── 2. Вебхук ────────────────────────────────────────────────────────────────

@router.post("/webhook", summary="Вебхук ЮKassa")
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
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
    payment.status = PaymentStatus.succeeded
    await db.flush()

    telegram_id = None
    message = ""

    if payment.entity_type == PaymentEntityType.ready_order:
        result = await db.execute(select(ReadyOrder).where(ReadyOrder.id == payment.entity_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = ReadyOrderStatus.paid
            user_r = await db.execute(select(User).where(User.id == order.user_id))
            user = user_r.scalar_one_or_none()
            if user:
                telegram_id = user.telegram_id
                message = (
                    f"✅ <b>Оплата прошла!</b>\n\n"
                    f"Заказ <b>№{order.id}</b> оплачен — {payment.amount} ₽\n"
                    f"Приступаем к сборке 📦"
                )

    elif payment.entity_type == PaymentEntityType.custom_order:
        result = await db.execute(select(CustomOrder).where(CustomOrder.id == payment.entity_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = CustomOrderStatus.paid
            user_r = await db.execute(select(User).where(User.id == order.user_id))
            user = user_r.scalar_one_or_none()
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