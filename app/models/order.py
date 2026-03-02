"""
app/models/order.py

Триггеры уведомлений через SQLAlchemy event.listen на after_update / after_insert.
Поскольку SQLAlchemy события синхронные, а уведомления асинхронные —
используем asyncio.ensure_future() для запуска корутин в фоне.

Логика триггеров:
  ReadyOrder:
    INSERT                     → notify_masters_ready_order_new
    status: paid               → notify_masters + notify_client
    status: assembling         → notify_client
    status: shipped            → notify_client
    status: done               → notify_client
    status: cancelled          → notify_masters + notify_client
    tracking_number → не None  → notify_client_ready_order_tracking

  CustomOrder:
    INSERT                     → notify_masters_custom_order_new + notify_client_custom_order_new
    status: reviewing          → notify_client
    status: accepted           → notify_client (платёжку шлём отдельно из API)
    status: paid               → notify_masters + notify_client
    status: in_work            → notify_client
    status: done               → notify_client
    status: cancelled          → notify_masters + notify_client
    tracking_number → не None  → notify_client_custom_order_tracking
"""
import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import anyio
from sqlalchemy import (
    String, Text, Numeric, Boolean, Integer,
    DateTime, ForeignKey, JSON, Enum as SAEnum, func, event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.utils.orders_notifications_cases import notify_masters_custom_order_new, notify_client_custom_order_new, \
    notify_client_ready_order_tracking, notify_client_ready_order_cancelled, notify_masters_ready_order_cancelled, \
    notify_client_ready_order_paid, notify_masters_ready_order_paid, notify_client_ready_order_assembling, \
    notify_client_ready_order_shipped, notify_client_ready_order_done, notify_masters_ready_order_new, \
    notify_client_custom_order_reviewing, notify_masters_custom_order_paid, notify_client_custom_order_paid, \
    notify_client_custom_order_in_work, notify_client_custom_order_done, notify_masters_custom_order_cancelled, \
    notify_client_custom_order_cancelled, notify_client_custom_order_tracking, notify_client_custom_order_accepted

logger = logging.getLogger(__name__)


# ── Статусы ───────────────────────────────────────────────────────────────────

class ReadyOrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid            = "paid"
    assembling      = "assembling"
    shipped         = "shipped"
    done            = "done"
    cancelled       = "cancelled"


class CustomOrderStatus(str, enum.Enum):
    new       = "new"
    reviewing = "reviewing"
    accepted  = "accepted"
    paid      = "paid"
    in_work   = "in_work"
    done      = "done"
    cancelled = "cancelled"


class DeliveryCarrier(str, enum.Enum):
    cdek   = "cdek"
    yandex = "yandex"


# ── Корзина ───────────────────────────────────────────────────────────────────

class CartItem(Base):
    __tablename__ = "cart_items"

    id:               Mapped[int]      = mapped_column(primary_key=True)
    user_id:          Mapped[int]      = mapped_column(ForeignKey("users.id"))
    ready_product_id: Mapped[int]      = mapped_column(ForeignKey("ready_products.id"))
    quantity:         Mapped[int]      = mapped_column(Integer, default=1)
    added_at:         Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user:          Mapped["User"]         = relationship(back_populates="cart_items")
    ready_product: Mapped["ReadyProduct"] = relationship(back_populates="cart_items")


# ── Заказ готового товара ─────────────────────────────────────────────────────

class ReadyOrder(Base):
    __tablename__ = "ready_orders"

    id:               Mapped[int]              = mapped_column(primary_key=True)
    user_id:          Mapped[int]              = mapped_column(ForeignKey("users.id"))
    status:           Mapped[ReadyOrderStatus] = mapped_column(
        SAEnum(ReadyOrderStatus, name="readyorderstatus"),
        default=ReadyOrderStatus.pending_payment,
    )
    total_price:      Mapped[Decimal]          = mapped_column(Numeric(10, 2))
    carrier:          Mapped[DeliveryCarrier]  = mapped_column(SAEnum(DeliveryCarrier, name="deliverycarrier_order"))
    delivery_name:    Mapped[str]              = mapped_column(String(200))
    delivery_phone:   Mapped[str]              = mapped_column(String(20))
    delivery_city:    Mapped[str]              = mapped_column(String(100))
    delivery_address: Mapped[str]              = mapped_column(String(500))
    tracking_number:  Mapped[str | None]       = mapped_column(String(200))
    created_at:       Mapped[datetime]         = mapped_column(DateTime, server_default=func.now())

    user:  Mapped["User"]                = relationship(back_populates="ready_orders")
    items: Mapped[list["ReadyOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


# ── Элементы заказа ───────────────────────────────────────────────────────────

class ReadyOrderItem(Base):
    __tablename__ = "ready_order_items"

    id:               Mapped[int]     = mapped_column(primary_key=True)
    order_id:         Mapped[int]     = mapped_column(ForeignKey("ready_orders.id"))
    ready_product_id: Mapped[int]     = mapped_column(ForeignKey("ready_products.id"))
    quantity:         Mapped[int]     = mapped_column(Integer, default=1)
    price_fixed:      Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order:         Mapped["ReadyOrder"]    = relationship(back_populates="items")
    ready_product: Mapped["ReadyProduct"] = relationship(back_populates="order_items")


# ── Кастомный заказ ───────────────────────────────────────────────────────────

class CustomOrder(Base):
    __tablename__ = "custom_orders"

    id:              Mapped[int]               = mapped_column(primary_key=True)
    user_id:         Mapped[int]               = mapped_column(ForeignKey("users.id"))
    product_type_id: Mapped[int]               = mapped_column(ForeignKey("product_types.id"))
    color_id:        Mapped[int]               = mapped_column(ForeignKey("colors.id"))
    size_label:      Mapped[str]               = mapped_column(String(10))
    print_id:        Mapped[int | None]        = mapped_column(ForeignKey("prints.id"), nullable=True)
    print_size_id:   Mapped[int | None]        = mapped_column(ForeignKey("print_sizes.id"), nullable=True)
    custom_images:   Mapped[list | None]       = mapped_column(JSON, nullable=True)
    comment:         Mapped[str | None]        = mapped_column(Text)
    recommended_price: Mapped[Decimal | None]  = mapped_column(Numeric(10, 2), nullable=True)
    final_price:       Mapped[Decimal | None]  = mapped_column(Numeric(10, 2), nullable=True)
    status:          Mapped[CustomOrderStatus] = mapped_column(
        SAEnum(CustomOrderStatus, name="customorderstatus"),
        default=CustomOrderStatus.new,
    )
    admin_comment:    Mapped[str | None]       = mapped_column(Text)
    tracking_number:  Mapped[str | None]       = mapped_column(String(200))   # ← новое поле
    carrier:          Mapped[DeliveryCarrier]  = mapped_column(SAEnum(DeliveryCarrier, name="deliverycarrier_custom"))
    delivery_name:    Mapped[str]              = mapped_column(String(200))
    delivery_phone:   Mapped[str]              = mapped_column(String(20))
    delivery_city:    Mapped[str]              = mapped_column(String(100))
    delivery_address: Mapped[str]              = mapped_column(String(500))
    created_at:       Mapped[datetime]         = mapped_column(DateTime, server_default=func.now())

    user:         Mapped["User"]             = relationship(back_populates="custom_orders")
    product_type: Mapped["ProductType"]      = relationship(back_populates="custom_orders")
    color:        Mapped["Color"]            = relationship()
    print:        Mapped["Print | None"]     = relationship()
    print_size:   Mapped["PrintSize | None"] = relationship()



# ── Статусы (без изменений) ───────────────────────────────────────────────────
class ReadyOrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    assembling = "assembling"
    shipped = "shipped"
    done = "done"
    cancelled = "cancelled"


class CustomOrderStatus(str, enum.Enum):
    new = "new"
    reviewing = "reviewing"
    accepted = "accepted"
    paid = "paid"
    in_work = "in_work"
    done = "done"
    cancelled = "cancelled"


class DeliveryCarrier(str, enum.Enum):
    cdek = "cdek"
    yandex = "yandex"


# ── Модели (без изменений) ────────────────────────────────────────────────────
# ... (CartItem, ReadyOrder, ReadyOrderItem, CustomOrder) — оставь как у тебя


# ─────────────────────────────────────────────────────────────────────────────
# FIRE — теперь правильно запускает async-функцию из любого потока
# ─────────────────────────────────────────────────────────────────────────────
def _fire(async_notify_func, order):
    """Запускаем async уведомление из синхронного SQLAlchemy event."""
    try:
        anyio.from_thread.run(async_notify_func, order)
    except Exception as e:
        logger.error(f"Notification fire error: {e}")


# ── ReadyOrder triggers ───────────────────────────────────────────────────────
@event.listens_for(ReadyOrder, "after_insert")
def _ready_order_created(mapper, connection, target):
    _ = target.user
    _fire(notify_masters_ready_order_new, target)


@event.listens_for(ReadyOrder, "after_update")
def _ready_order_updated(mapper, connection, target):
    _ = target.user

    from sqlalchemy.orm import attributes
    status_hist = attributes.get_history(target, "status")
    tracking_hist = attributes.get_history(target, "tracking_number")

    old_status = status_hist.deleted[0] if status_hist.has_changes() and status_hist.deleted else None
    new_status = target.status

    if old_status and old_status != new_status:
        if new_status == ReadyOrderStatus.paid:
            _fire(notify_masters_ready_order_paid, target)
            _fire(notify_client_ready_order_paid, target)
        elif new_status == ReadyOrderStatus.assembling:
            _fire(notify_client_ready_order_assembling, target)
        elif new_status == ReadyOrderStatus.shipped:
            _fire(notify_client_ready_order_shipped, target)
        elif new_status == ReadyOrderStatus.done:
            _fire(notify_client_ready_order_done, target)
        elif new_status == ReadyOrderStatus.cancelled:
            _fire(notify_masters_ready_order_cancelled, target)
            _fire(notify_client_ready_order_cancelled, target)

    # Трек-номер появился
    old_tracking = tracking_hist.deleted[0] if tracking_hist.has_changes() and tracking_hist.deleted else None
    if target.tracking_number and not old_tracking:
        _fire(notify_client_ready_order_tracking, target)


# ── CustomOrder triggers ──────────────────────────────────────────────────────
@event.listens_for(CustomOrder, "after_insert")
def _custom_order_created(mapper, connection, target):
    _ = target.user
    _ = target.product_type
    _fire(notify_masters_custom_order_new, target)
    _fire(notify_client_custom_order_new, target)


@event.listens_for(CustomOrder, "after_update")
def receive_custom_order_updated(mapper, connection, target):
    user = target.user
    _ = target.product_type
    from sqlalchemy.orm import attributes
    status_hist = attributes.get_history(target, "status")
    tracking_hist = attributes.get_history(target, "tracking_number")

    old_status = status_hist.deleted[0] if status_hist.has_changes() and status_hist.deleted else None
    new_status = target.status

    if old_status and old_status != new_status:
        if new_status == CustomOrderStatus.reviewing:
            _fire(notify_client_custom_order_reviewing, target)
        elif new_status == CustomOrderStatus.accepted:
            _fire(notify_client_custom_order_accepted, target)
        elif new_status == CustomOrderStatus.paid:
            _fire(notify_masters_custom_order_paid, target)
            _fire(notify_client_custom_order_paid, target)
        elif new_status == CustomOrderStatus.in_work:
            _fire(notify_client_custom_order_in_work, target)
        elif new_status == CustomOrderStatus.done:
            _fire(notify_client_custom_order_done, target)
        elif new_status == CustomOrderStatus.cancelled:
            _fire(notify_masters_custom_order_cancelled, target)
            _fire(notify_client_custom_order_cancelled, target)

    # Трек-номер появился
    old_tracking = tracking_hist.deleted[0] if tracking_hist.has_changes() and tracking_hist.deleted else None
    if target.tracking_number and not old_tracking:
        _fire(notify_client_custom_order_tracking, target)