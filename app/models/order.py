from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Boolean, Integer,
    DateTime, ForeignKey, JSON, Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


# ── Статусы ───────────────────────────────────────────────────────────────────

class ReadyOrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid            = "paid"
    assembling      = "assembling"
    shipped         = "shipped"
    done            = "done"
    cancelled       = "cancelled"


class CustomOrderStatus(str, enum.Enum):
    new       = "new"         # заявка отправлена
    reviewing = "reviewing"   # админ смотрит
    accepted  = "accepted"    # принят → клиенту уходит платёжка
    paid      = "paid"        # оплачен → можно приступать
    in_work   = "in_work"     # в работе
    done      = "done"        # готово
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

    # Снапшот данных доставки на момент заказа
    carrier:          Mapped[DeliveryCarrier]  = mapped_column(SAEnum(DeliveryCarrier, name="deliverycarrier_order"))
    delivery_name:    Mapped[str]              = mapped_column(String(200))
    delivery_phone:   Mapped[str]              = mapped_column(String(20))
    delivery_city:    Mapped[str]              = mapped_column(String(100))
    delivery_address: Mapped[str]              = mapped_column(String(500))
    tracking_number:  Mapped[str | None]       = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user:  Mapped["User"]                = relationship(back_populates="ready_orders")
    items: Mapped[list["ReadyOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class ReadyOrderItem(Base):
    __tablename__ = "ready_order_items"

    id:               Mapped[int]     = mapped_column(primary_key=True)
    order_id:         Mapped[int]     = mapped_column(ForeignKey("ready_orders.id"))
    ready_product_id: Mapped[int]     = mapped_column(ForeignKey("ready_products.id"))
    quantity:         Mapped[int]     = mapped_column(Integer, default=1)
    price_fixed:      Mapped[Decimal] = mapped_column(Numeric(10, 2))  # цена на момент заказа

    order:         Mapped["ReadyOrder"]    = relationship(back_populates="items")
    ready_product: Mapped["ReadyProduct"] = relationship(back_populates="order_items")


# ── Кастомный заказ (вышивка) ─────────────────────────────────────────────────

class CustomOrder(Base):
    __tablename__ = "custom_orders"

    id:              Mapped[int]               = mapped_column(primary_key=True)
    user_id:         Mapped[int]               = mapped_column(ForeignKey("users.id"))
    product_type_id: Mapped[int]               = mapped_column(ForeignKey("product_types.id"))
    color_id:        Mapped[int]               = mapped_column(ForeignKey("colors.id"))
    size_label:      Mapped[str]               = mapped_column(String(10))

    # Вышивка — либо из каталога, либо своё фото
    print_id:        Mapped[int | None]        = mapped_column(ForeignKey("prints.id"), nullable=True)
    print_size_id:   Mapped[int | None]        = mapped_column(ForeignKey("print_sizes.id"), nullable=True)
    custom_images:   Mapped[list | None]       = mapped_column(JSON, nullable=True)   # ["url1","url2"]
    comment:         Mapped[str | None]        = mapped_column(Text)

    # Цены
    recommended_price: Mapped[Decimal | None]  = mapped_column(Numeric(10, 2), nullable=True)
    # base_price + print_size.price (если выбран принт), иначе только base_price
    final_price:       Mapped[Decimal | None]  = mapped_column(Numeric(10, 2), nullable=True)
    # выставляет/корректирует админ, дефолт = recommended_price

    status:          Mapped[CustomOrderStatus] = mapped_column(
                         SAEnum(CustomOrderStatus, name="customorderstatus"),
                         default=CustomOrderStatus.new,
                     )
    admin_comment:   Mapped[str | None]        = mapped_column(Text)

    # Снапшот доставки
    carrier:          Mapped[DeliveryCarrier]  = mapped_column(SAEnum(DeliveryCarrier, name="deliverycarrier_custom"))
    delivery_name:    Mapped[str]              = mapped_column(String(200))
    delivery_phone:   Mapped[str]              = mapped_column(String(20))
    delivery_city:    Mapped[str]              = mapped_column(String(100))
    delivery_address: Mapped[str]              = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user:         Mapped["User"]        = relationship(back_populates="custom_orders")
    product_type: Mapped["ProductType"] = relationship(back_populates="custom_orders")
    color:        Mapped["Color"]       = relationship()
    print:        Mapped["Print | None"]     = relationship()
    print_size:   Mapped["PrintSize | None"] = relationship()