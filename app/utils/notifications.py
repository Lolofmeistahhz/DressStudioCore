import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_API = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"
_ADMIN_URL = settings.ADMIN_BASE_URL.rstrip("/")


async def _send(chat_id: int | str, text: str, reply_markup: dict | None = None) -> bool:
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{_API}/sendMessage", json=payload)
            if not r.is_success:
                logger.error(f"TG notify error {r.status_code}: {r.text}")
                return False
            return True
    except Exception as e:
        logger.error(f"TG notify exception: {e}")
        return False


def _admin_link(section: str, obj_id: int, action: str = "detail") -> str:
    """Ссылка на запись в starlette-admin."""
    return f"{_ADMIN_URL}/{section}/{action}/{obj_id}"


def _inline_kb(text: str, url: str) -> dict:
    return {"inline_keyboard": [[{"text": text, "url": url}]]}


# ─────────────────────────────────────────────────────────────────────────────
# Уведомления мастерам
# ─────────────────────────────────────────────────────────────────────────────

async def notify_masters_ready_order_new(order) -> None:
    """Новый заказ обычного мерча."""
    user = order.user
    text = (
        f"🛍 <b>Новый заказ мерча #{order.id}</b>\n\n"
        f"Покупатель: {user.delivery_name or user.full_name or '—'}\n"
        f"Телефон: {user.phone or '—'}\n"
        f"Сумма: <b>{order.total_price} ₽</b>\n"
        f"Доставка: {order.delivery_city}, {order.delivery_address}"
    )
    await _send(
        settings.ALERT_CHAT_ID, text,
        _inline_kb("📋 Открыть в админке", _admin_link("readyorder", order.id)),
    )


async def notify_masters_ready_order_paid(order) -> None:
    """Обычный заказ оплачен — нужен трек."""
    user = order.user
    text = (
        f"💳 <b>Заказ мерча #{order.id} оплачен!</b>\n\n"
        f"Покупатель: {user.delivery_name or user.full_name or '—'}\n"
        f"Телефон: {user.phone or '—'}\n"
        f"Адрес: {order.delivery_city}, {order.delivery_address}\n\n"
        f"⬆️ Добавьте трек-номер в заказе"
    )
    await _send(
        settings.ALERT_CHAT_ID, text,
        _inline_kb("✏️ Добавить трек-номер", _admin_link("readyorder", order.id, "edit")),
    )


async def notify_masters_ready_order_cancelled(order) -> None:
    text = (
        f"❌ <b>Заказ мерча #{order.id} отменён</b>\n"
        f"Покупатель: {order.user.delivery_name or '—'}"
    )
    await _send(settings.ALERT_CHAT_ID, text)


async def notify_masters_custom_order_new(order) -> None:
    """Новый кастомный заказ — нужно связаться с клиентом."""
    user = order.user
    comment_line = f"\n💬 Комментарий: <i>{order.comment}</i>" if order.comment else ""
    images_line  = f"\n📷 Фото вышивки: {len(order.custom_images)} шт." if order.custom_images else ""
    text = (
        f"🧵 <b>Новый кастомный заказ #{order.id}</b>\n\n"
        f"Покупатель: {user.delivery_name or user.full_name or '—'}\n"
        f"Телефон: <b>{user.phone or '—'}</b>\n"
        f"Telegram: @{user.username or '—'} (ID: <code>{user.telegram_id}</code>)\n"
        f"Изделие: {order.product_type.name}, размер {order.size_label}"
        f"{comment_line}{images_line}\n\n"
        f"👆 Уточните детали и смените статус на <b>accepted</b>"
    )
    await _send(
        settings.ALERT_CHAT_ID, text,
        _inline_kb("📋 Открыть в админке", _admin_link("customorder", order.id)),
    )


async def notify_masters_custom_order_paid(order) -> None:
    """Кастомный заказ оплачен — нужно выполнить и добавить трек."""
    user = order.user
    text = (
        f"💳 <b>Кастомный заказ #{order.id} оплачен!</b>\n\n"
        f"Покупатель: {user.delivery_name or user.full_name or '—'}\n"
        f"Телефон: {user.phone or '—'}\n"
        f"Изделие: {order.product_type.name}, {order.size_label}\n\n"
        f"🔨 Приступайте к работе! После отправки — добавьте трек-номер"
    )
    await _send(
        settings.ALERT_CHAT_ID, text,
        _inline_kb("✏️ Добавить трек-номер", _admin_link("customorder", order.id, "edit")),
    )


async def notify_masters_custom_order_cancelled(order) -> None:
    text = (
        f"❌ <b>Кастомный заказ #{order.id} отменён</b>\n"
        f"Покупатель: {order.user.delivery_name or '—'}"
    )
    await _send(settings.ALERT_CHAT_ID, text)


# ─────────────────────────────────────────────────────────────────────────────
# Уведомления клиенту
# ─────────────────────────────────────────────────────────────────────────────

async def notify_client_ready_order_paid(order) -> None:
    await _send(
        order.user.telegram_id,
        f"✅ <b>Оплата подтверждена!</b>\n\n"
        f"Заказ <b>#{order.id}</b> передан в обработку.\n"
        f"Как только посылка будет отправлена — вы получите трек-номер.",
    )


async def notify_client_ready_order_assembling(order) -> None:
    await _send(
        order.user.telegram_id,
        f"📦 Заказ <b>#{order.id}</b> собирается и скоро отправится к вам!",
    )


async def notify_client_ready_order_shipped(order) -> None:
    """Статус shipped без трека — просто информируем."""
    await _send(
        order.user.telegram_id,
        f"🚚 Заказ <b>#{order.id}</b> передан в службу доставки.\n"
        f"Трек-номер появится совсем скоро.",
    )


async def notify_client_ready_order_tracking(order) -> None:
    """Трек-номер добавлен."""
    carrier_map = {"cdek": "СДЭК", "yandex": "Яндекс Доставка"}
    carrier_name = carrier_map.get(str(order.carrier or ""), "службу доставки")
    await _send(
        order.user.telegram_id,
        f"📦 <b>Ваш заказ #{order.id} отправлен!</b>\n\n"
        f"Служба доставки: {carrier_name}\n"
        f"Трек-номер: <code>{order.tracking_number}</code>\n\n"
        f"Отслеживайте посылку на сайте перевозчика.",
    )


async def notify_client_ready_order_done(order) -> None:
    await _send(
        order.user.telegram_id,
        f"🎉 <b>Заказ #{order.id} доставлен!</b>\n\n"
        f"Спасибо за покупку! Будем рады видеть вас снова 🧵",
    )


async def notify_client_ready_order_cancelled(order) -> None:
    await _send(
        order.user.telegram_id,
        f"❌ <b>Заказ #{order.id} отменён.</b>\n\n"
        f"Если у вас есть вопросы — напишите нам напрямую.",
    )


async def notify_client_custom_order_new(order) -> None:
    await _send(
        order.user.telegram_id,
        f"🧵 <b>Заявка на кастомный заказ #{order.id} принята!</b>\n\n"
        f"Мы изучим детали и свяжемся с вами для уточнений.\n"
        f"Ожидайте — обычно это занимает до 24 часов.",
    )


async def notify_client_custom_order_reviewing(order) -> None:
    await _send(
        order.user.telegram_id,
        f"🔍 Ваша заявка <b>#{order.id}</b> уже рассматривается мастером.\n"
        f"Скоро получите ответ!",
    )


async def notify_client_custom_order_accepted(order, payment_url: str | None = None) -> None:
    """Заказ одобрен — отправляем платёжную ссылку."""
    price_line = f"Сумма к оплате: <b>{order.final_price} ₽</b>\n\n" if order.final_price else ""
    text = (
        f"✅ <b>Ваш кастомный заказ #{order.id} одобрен!</b>\n\n"
        f"{price_line}"
        f"Для начала работы необходима оплата."
    )
    kb = _inline_kb("💳 Оплатить", payment_url) if payment_url else None
    await _send(order.user.telegram_id, text, kb)


async def notify_client_custom_order_paid(order) -> None:
    await _send(
        order.user.telegram_id,
        f"💳 <b>Оплата кастомного заказа #{order.id} получена!</b>\n\n"
        f"Мастер приступает к работе. "
        f"Мы уведомим вас когда заказ будет готов к отправке.",
    )


async def notify_client_custom_order_in_work(order) -> None:
    await _send(
        order.user.telegram_id,
        f"🔨 Ваш кастомный заказ <b>#{order.id}</b> уже в работе у мастера!\n"
        f"Совсем скоро он будет готов.",
    )


async def notify_client_custom_order_tracking(order) -> None:
    carrier_map = {"cdek": "СДЭК", "yandex": "Яндекс Доставка"}
    carrier_name = carrier_map.get(str(order.carrier or ""), "службу доставки")
    await _send(
        order.user.telegram_id,
        f"📦 <b>Ваш кастомный заказ #{order.id} готов и отправлен!</b>\n\n"
        f"Служба доставки: {carrier_name}\n"
        f"Трек-номер: <code>{order.tracking_number}</code>\n\n"
        f"Спасибо, что выбрали нас 🧵",
    )


async def notify_client_custom_order_done(order) -> None:
    await _send(
        order.user.telegram_id,
        f"🎉 <b>Кастомный заказ #{order.id} доставлен!</b>\n\n"
        f"Надеемся, что вы в восторге от работы наших мастеров!\n"
        f"Будем рады видеть вас снова 💛",
    )


async def notify_client_custom_order_cancelled(order) -> None:
    comment_line = f"\n\nКомментарий: <i>{order.admin_comment}</i>" if order.admin_comment else ""
    await _send(
        order.user.telegram_id,
        f"❌ <b>Кастомный заказ #{order.id} отменён.</b>{comment_line}\n\n"
        f"Если есть вопросы — напишите нам напрямую.",
    )