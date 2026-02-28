import logging

import httpx
from requests import Session

from app.core.config import settings
from app.models import Appointment

logger = logging.getLogger(__name__)

def notify_telegram_sync(telegram_id: int, text: str) -> None:


    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    try:
        with httpx.Client(timeout=5) as client:
            r = client.post(url, json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "HTML",
            })
            logger.info(f"Telegram response {r.status_code} для telegram_id={telegram_id}")
    except Exception as e:
        logger.warning(f"Ошибка уведомления telegram_id={telegram_id}: {e}")


def send_payment_link(appt: Appointment, session: Session, telegram_id: int) -> None:
    from app.core.config import settings
    from app.models.payment import Payment as PaymentModel, PaymentEntityType

    if not appt.final_price:
        logger.warning(f"Запись {appt.id}: final_price не задана")
        notify_telegram_sync(
            telegram_id,
            f"✅ Ваш заказ <b>№{appt.id}</b> выполнен!\n\n"
            f"⚠️ Сумма не указана. Свяжитесь с администратором.",
        )
        return

    try:
        from yookassa import Configuration, Payment as YKPayment
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

        webhook_base = settings.WEBHOOK_URL.rstrip("/")
        yk_payment = YKPayment.create({
            "amount": {"value": f"{appt.final_price:.2f}", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{webhook_base}/api/v1/payments/success",
            },
            "capture": True,
            "description": f"Услуги ателье по записи №{appt.id}",
            "metadata": {
                "entity_type": "appointment",
                "entity_id": str(appt.id),
            },
        })

        payment = PaymentModel(
            entity_type=PaymentEntityType.appointment,
            entity_id=appt.id,
            amount=appt.final_price,
            yookassa_payment_id=yk_payment.id,
        )
        session.add(payment)
        session.commit()

        confirmation_url = yk_payment.confirmation.confirmation_url
        logger.info(f"Платёж создан для записи {appt.id}: {confirmation_url}")

        notify_telegram_sync(
            telegram_id,
            f"✅ Ваш заказ <b>№{appt.id}</b> выполнен!\n\n"
            f"Сумма к оплате: <b>{appt.final_price} ₽</b>\n\n"
            f'Для оплаты: <a href="{confirmation_url}">💳 Оплатить онлайн</a>',
        )

    except Exception as e:
        logger.error(f"Ошибка создания платежа для записи {appt.id}: {e}", exc_info=True)
        notify_telegram_sync(
            telegram_id,
            f"✅ Ваш заказ <b>№{appt.id}</b> выполнен!\n"
            f"Сумма: <b>{appt.final_price} ₽</b>\n\n"
            f"Свяжитесь с нами для оплаты.",
        )


def _get_str(val) -> str:
    """Enum или строка → строка."""
    return val.value if hasattr(val, "value") else str(val)
