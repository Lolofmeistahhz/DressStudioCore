import logging
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from yookassa import Configuration, Payment as YKPayment

from app.core.database import AsyncSessionLocal
from app.models.payment import Payment, PaymentEntityType
from app.schemas.payment import  PaymentInitResponse

logger = logging.getLogger(__name__)


def _get_str(val) -> str:
    """Enum или строка → строка."""
    return val.value if hasattr(val, "value") else str(val)


def media_url(path: str | None) -> str | None:
    """
    /media/abc.jpg  →  https://yourdomain.com/media/abc.jpg
    None или пустая строка → None
    Уже полный URL → возвращаем как есть.
    """
    if not path:
        return None
    if path.startswith("http"):
        return path
    base = settings.BASE_URL.rstrip("/")
    return f"{base}{path}"


async def save_uploaded_file(file) -> str | None:
    if not file or not hasattr(file, "filename") or not file.filename:
        return None
    try:
        ext      = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / filename
        content   = await file.read()
        file_path.write_bytes(content)

        # Возвращаем только путь — media_url() добавит домен при отдаче
        return f"/media/{filename}"
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return None


def _yookassa():
    try:
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        return YKPayment
    except ImportError:
        raise HTTPException(status_code=503, detail="pip install yookassa")


async def create_payment_for_order(
    entity_type: PaymentEntityType,
    entity_id: int,
    amount: Decimal,
    db: AsyncSessionLocal
) -> PaymentInitResponse:
    """
    Создает платеж для заказа и возвращает данные для оплаты.
    """
    YKPayment = _yookassa()

    descriptions = {
        PaymentEntityType.ready_order: f"Заказ готового мерча №{entity_id}",
        PaymentEntityType.custom_order: f"Кастомный заказ №{entity_id}",
        PaymentEntityType.constructor_order: f"Заказ из конструктора №{entity_id}",
    }

    webhook_base = settings.WEBHOOK_URL.rstrip("/")
    yk_payment = YKPayment.create({
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": f"{webhook_base}/api/v1/payments/success",
        },
        "capture": True,
        "description": descriptions[entity_type],
        "metadata": {
            "entity_type": entity_type.value,
            "entity_id": str(entity_id),
        },
    })

    payment = Payment(
        entity_type=entity_type,
        entity_id=entity_id,
        amount=amount,
        yookassa_payment_id=yk_payment.id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentInitResponse(
        payment_id=payment.id,
        yookassa_payment_id=yk_payment.id,
        confirmation_url=yk_payment.confirmation.confirmation_url,
        amount=amount,
    )