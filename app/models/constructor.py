"""
app/models/constructor.py

Задел под WebApp конструктор.
Таблицы создаются сейчас, логика — в отдельном репозитории позже.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Boolean, Integer,
    DateTime, ForeignKey, JSON, Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ConstructorOrderStatus(str, enum.Enum):
    new       = "new"
    reviewing = "reviewing"
    accepted  = "accepted"
    paid      = "paid"
    in_work   = "in_work"
    done      = "done"
    cancelled = "cancelled"


class CanvasTemplate(Base):
    """
    Шаблон изделия для конструктора.
    canvas_image_url — реальное фото изделия (нужно для наложения принта).
    embroidery_zones — JSON: [{x, y, w, h, label}] — допустимые зоны размещения.
    """
    __tablename__ = "canvas_templates"

    id:               Mapped[int]        = mapped_column(primary_key=True)
    product_type_id:  Mapped[int]        = mapped_column(ForeignKey("product_types.id"))
    color_id:         Mapped[int]        = mapped_column(ForeignKey("colors.id"))
    canvas_image_url: Mapped[str | None] = mapped_column(String(500))
    width_px:         Mapped[int | None] = mapped_column(Integer)
    height_px:        Mapped[int | None] = mapped_column(Integer)
    width_cm:         Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    height_cm:        Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    embroidery_zones: Mapped[list | None]    = mapped_column(JSON, nullable=True)
    is_active:        Mapped[bool]       = mapped_column(Boolean, default=False)

    product_type: Mapped["ProductType"] = relationship()
    color:        Mapped["Color"]       = relationship()
    orders:       Mapped[list["ConstructorOrder"]] = relationship(back_populates="canvas_template")


class ConstructorOrder(Base):
    """
    Заказ из конструктора.
    placements — JSON: [{print_id, x, y, w_cm, h_cm}]
    """
    __tablename__ = "constructor_orders"

    id:                 Mapped[int]        = mapped_column(primary_key=True)
    user_id:            Mapped[int]        = mapped_column(ForeignKey("users.id"))
    canvas_template_id: Mapped[int]        = mapped_column(ForeignKey("canvas_templates.id"))
    placements:         Mapped[list | None] = mapped_column(JSON, nullable=True)
    snapshot_url:       Mapped[str | None] = mapped_column(String(500))
    recommended_price:  Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    final_price:        Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status:             Mapped[ConstructorOrderStatus] = mapped_column(
                            SAEnum(ConstructorOrderStatus, name="constructororderstatus"),
                            default=ConstructorOrderStatus.new,
                        )
    admin_comment:      Mapped[str | None] = mapped_column(Text)
    carrier:            Mapped[str | None] = mapped_column(String(20))
    delivery_name:      Mapped[str | None] = mapped_column(String(200))
    delivery_phone:     Mapped[str | None] = mapped_column(String(20))
    delivery_city:      Mapped[str | None] = mapped_column(String(100))
    delivery_address:   Mapped[str | None] = mapped_column(String(500))
    created_at:         Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())

    canvas_template: Mapped["CanvasTemplate"] = relationship(back_populates="orders")
    user: Mapped["User"] = relationship(back_populates="constructor_orders")