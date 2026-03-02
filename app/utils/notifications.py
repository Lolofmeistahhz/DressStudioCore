import logging
import httpx
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_API = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"
_ADMIN_URL = settings.ADMIN_BASE_URL.rstrip("/")


async def send_telegram_message(
        chat_id: int | str,
        text: str,
        reply_markup: dict | None = None
) -> bool:
    """Отправка сообщения в Telegram."""
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{_API}/sendMessage", json=payload)
            if not response.is_success:
                logger.error(f"TG notify error {response.status_code}: {response.text}")
                return False
            return True
    except Exception as e:
        logger.error(f"TG notify exception: {e}")
        return False


def admin_link(section: str, obj_id: int, action: str = "detail") -> str:
    """Ссылка на запись в starlette-admin."""
    return f"{_ADMIN_URL}/{section}/{action}/{obj_id}"


def inline_keyboard(text: str, url: str) -> dict:
    """Создает inline клавиатуру с одной кнопкой."""
    return {"inline_keyboard": [[{"text": text, "url": url}]]}