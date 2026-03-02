import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.utils.shared import create_payment_for_order
from app.models.payment import PaymentEntityType
from app.utils.notifications import (
    send_telegram_message,
    admin_link,
    inline_keyboard
)

logger = logging.getLogger(__name__)




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
    await send_telegram_message(
        settings.ALERTCHAT_ID,
        text,
        inline_keyboard("📋 Открыть в админке", admin_link("ready-order", order.id))
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
    await send_telegram_message(
        settings.ALERT_CHAT_ID,
        text,
        inline_keyboard("✏️ Добавить трек-номер", admin_link("ready-order", order.id, "edit"))
    )


async def notify_masters_ready_order_cancelled(order) -> None:
    text = (
        f"❌ <b>Заказ мерча #{order.id} отменён</b>\n"
        f"Покупатель: {order.user.delivery_name or '—'}"
    )
    await send_telegram_message(settings.ALERT_CHAT_ID, text)


async def notify_masters_custom_order_new(order) -> None:
    """Новый кастомный заказ — нужно связаться с клиентом."""
    user = order.user
    comment_line = f"\n💬 Комментарий: <i>{order.comment}</i>" if order.comment else ""
    images_line = f"\n📷 Фото вышивки: {len(order.custom_images)} шт." if order.custom_images else ""
    text = (
        f"🧵 <b>Новый кастомный заказ #{order.id}</b>\n\n"
        f"Покупатель: {user.delivery_name or user.full_name or '—'}\n"
        f"Телефон: <b>{user.phone or '—'}</b>\n"
        f"Telegram: @{user.username or '—'} (ID: <code>{user.telegram_id}</code>)\n"
        f"Изделие: {order.product_type.name}, размер {order.size_label}"
        f"{comment_line}{images_line}\n\n"
        f"👆 Уточните детали и смените статус на <b>accepted</b>"
    )
    await send_telegram_message(
        settings.ALERT_CHAT_ID,
        text,
        inline_keyboard("📋 Открыть в админке", admin_link("custom-order", order.id))
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
    await send_telegram_message(
        settings.ALERT_CHAT_ID,
        text,
        inline_keyboard("✏️ Добавить трек-номер", admin_link("custom-order", order.id, "edit"))
    )


async def notify_masters_custom_order_cancelled(order) -> None:
    text = (
        f"❌ <b>Кастомный заказ #{order.id} отменён</b>\n"
        f"Покупатель: {order.user.delivery_name or '—'}"
    )
    await send_telegram_message(settings.ALERT_CHAT_ID, text)


# ─────────────────────────────────────────────────────────────────────────────
# Уведомления клиенту
# ─────────────────────────────────────────────────────────────────────────────

async def notify_client_ready_order_paid(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"✅ <b>Оплата подтверждена!</b>\n\n"
        f"Заказ <b>#{order.id}</b> передан в обработку.\n"
        f"Как только посылка будет отправлена — вы получите трек-номер."
    )


async def notify_client_ready_order_assembling(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"📦 Заказ <b>#{order.id}</b> собирается и скоро отправится к вам!"
    )


async def notify_client_ready_order_shipped(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🚚 Заказ <b>#{order.id}</b> передан в службу доставки.\n"
        f"Трек-номер появится совсем скоро."
    )


async def notify_client_ready_order_tracking(order) -> None:
    carrier_map = {"cdek": "СДЭК", "yandex": "Яндекс Доставка"}
    carrier_name = carrier_map.get(str(order.carrier or ""), "службу доставки")
    await send_telegram_message(
        order.user.telegram_id,
        f"📦 <b>Ваш заказ #{order.id} отправлен!</b>\n\n"
        f"Служба доставки: {carrier_name}\n"
        f"Трек-номер: <code>{order.tracking_number}</code>\n\n"
        f"Отслеживайте посылку на сайте перевозчика."
    )


async def notify_client_ready_order_done(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🎉 <b>Заказ #{order.id} доставлен!</b>\n\n"
        f"Спасибо за покупку! Будем рады видеть вас снова 🧵"
    )


async def notify_client_ready_order_cancelled(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"❌ <b>Заказ #{order.id} отменён.</b>\n\n"
        f"Если у вас есть вопросы — напишите нам напрямую."
    )


async def notify_client_custom_order_new(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🧵 <b>Заявка на кастомный заказ #{order.id} принята!</b>\n\n"
        f"Мы изучим детали и свяжемся с вами для уточнений.\n"
        f"Ожидайте — обычно это занимает до 24 часов."
    )


async def notify_client_custom_order_reviewing(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🔍 Ваша заявка <b>#{order.id}</b> уже рассматривается мастером.\n"
        f"Скоро получите ответ!"
    )


async def notify_client_custom_order_accepted(order):
    """Кастомный заказ одобрен - отправляем клиенту ссылку на оплату."""
    logger.info(f"Custom order #{order.id} accepted, creating payment")

    try:
        async with AsyncSessionLocal() as db:
            payment_init = await create_payment_for_order(
                entity_type=PaymentEntityType.custom_order,
                entity_id=order.id,
                amount=order.final_price or order.recommended_price,
                db=db
            )

            text = (
                f"✅ <b>Ваш кастомный заказ №{order.id} одобрен!</b>\n\n"
                f"Сумма к оплате: <b>{order.final_price or order.recommended_price} ₽</b>\n\n"
                f"Для начала работы над заказом необходима оплата."
            )

            await send_telegram_message(
                chat_id=order.user.telegram_id,
                text=text,
                reply_markup=inline_keyboard("💳 Оплатить", payment_init.confirmation_url)
            )

            logger.info(f"Payment link sent for order #{order.id}")

    except Exception as e:
        logger.error(f"Failed to send payment link for order #{order.id}: {e}")
        try:
            await send_telegram_message(
                settings.ALERT_CHAT_ID,
                text=f"⚠️ Ошибка отправки платежной ссылки для заказа #{order.id}: {e}"
            )
        except:
            pass


async def notify_client_custom_order_paid(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"💳 <b>Оплата кастомного заказа #{order.id} получена!</b>\n\n"
        f"Мастер приступает к работе. "
        f"Мы уведомим вас когда заказ будет готов к отправке."
    )


async def notify_client_custom_order_in_work(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🔨 Ваш кастомный заказ <b>#{order.id}</b> уже в работе у мастера!\n"
        f"Совсем скоро он будет готов."
    )


async def notify_client_custom_order_tracking(order) -> None:
    carrier_map = {"cdek": "СДЭК", "yandex": "Яндекс Доставка"}
    carrier_name = carrier_map.get(str(order.carrier or ""), "службу доставки")
    await send_telegram_message(
        order.user.telegram_id,
        f"📦 <b>Ваш кастомный заказ #{order.id} готов и отправлен!</b>\n\n"
        f"Служба доставки: {carrier_name}\n"
        f"Трек-номер: <code>{order.tracking_number}</code>\n\n"
        f"Спасибо, что выбрали нас 🧵"
    )


async def notify_client_custom_order_done(order) -> None:
    await send_telegram_message(
        order.user.telegram_id,
        f"🎉 <b>Кастомный заказ #{order.id} доставлен!</b>\n\n"
        f"Надеемся, что вы в восторге от работы наших мастеров!\n"
        f"Будем рады видеть вас снова 💛"
    )


async def notify_client_custom_order_cancelled(order) -> None:
    comment_line = f"\n\nКомментарий: <i>{order.admin_comment}</i>" if order.admin_comment else ""
    await send_telegram_message(
        order.user.telegram_id,
        f"❌ <b>Кастомный заказ #{order.id} отменён.</b>{comment_line}\n\n"
        f"Если есть вопросы — напишите нам напрямую."
    )

