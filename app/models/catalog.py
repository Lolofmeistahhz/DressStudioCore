from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Boolean, Integer,
    ForeignKey, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Цвет ──────────────────────────────────────────────────────────────────────

class Color(Base):
    __tablename__ = "colors"

    id:                Mapped[int]        = mapped_column(primary_key=True)
    name:              Mapped[str]        = mapped_column(String(100))
    hex_code:          Mapped[str]        = mapped_column(String(7))    # #RRGGBB

    product_type_colors: Mapped[list["ProductTypeColor"]] = relationship(back_populates="color")


# ── Тип изделия ───────────────────────────────────────────────────────────────

class ProductType(Base):
    __tablename__ = "product_types"

    id:             Mapped[int]        = mapped_column(primary_key=True)
    name:           Mapped[str]        = mapped_column(String(100))         # Футболка
    slug:           Mapped[str]        = mapped_column(String(50), unique=True)  # t_shirt
    base_price:     Mapped[Decimal]    = mapped_column(Numeric(10, 2))
    description:    Mapped[str | None] = mapped_column(Text)
    image_url:      Mapped[str | None] = mapped_column(String(500))         # фото изделия
    size_chart_url: Mapped[str | None] = mapped_column(String(500))         # таблица размеров
    color_palette_url: Mapped[str | None] = mapped_column(String(500))  # общая палитра
    composition:    Mapped[str | None] = mapped_column(String(500))         # состав ткани
    notes:          Mapped[str | None] = mapped_column(Text)
    is_active:      Mapped[bool]       = mapped_column(Boolean, default=True)

    sizes:  Mapped[list["ProductTypeSize"]]  = relationship(back_populates="product_type", cascade="all, delete-orphan")
    colors: Mapped[list["ProductTypeColor"]] = relationship(back_populates="product_type", cascade="all, delete-orphan")
    ready_products: Mapped[list["ReadyProduct"]] = relationship(back_populates="product_type")
    custom_orders:  Mapped[list["CustomOrder"]]  = relationship(back_populates="product_type")


# ── Размеры типа изделия ──────────────────────────────────────────────────────

class ProductTypeSize(Base):
    __tablename__ = "product_type_sizes"

    id:              Mapped[int]        = mapped_column(primary_key=True)
    product_type_id: Mapped[int]        = mapped_column(ForeignKey("product_types.id"))
    label:           Mapped[str]        = mapped_column(String(10))   # XS / S / M / L / XL ...
    length:          Mapped[str | None] = mapped_column(String(20))
    width:           Mapped[str | None] = mapped_column(String(20))
    sleeve:          Mapped[str | None] = mapped_column(String(20))
    shoulders:       Mapped[str | None] = mapped_column(String(20))
    waist_width:     Mapped[str | None] = mapped_column(String(20))   # только для свитшотов

    product_type: Mapped["ProductType"] = relationship(back_populates="sizes")


# ── Доступные цвета для типа изделия ─────────────────────────────────────────

class ProductTypeColor(Base):
    __tablename__ = "product_type_colors"

    id:              Mapped[int]  = mapped_column(primary_key=True)
    product_type_id: Mapped[int]  = mapped_column(ForeignKey("product_types.id"))
    color_id:        Mapped[int]  = mapped_column(ForeignKey("colors.id"))
    in_stock:        Mapped[bool] = mapped_column(Boolean, default=True)

    product_type: Mapped["ProductType"] = relationship(back_populates="colors")
    color:        Mapped["Color"]       = relationship(back_populates="product_type_colors")


# ── Принт / вышивка ───────────────────────────────────────────────────────────

class Print(Base):
    __tablename__ = "prints"

    id:        Mapped[int]        = mapped_column(primary_key=True)
    name:      Mapped[str]        = mapped_column(String(200))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool]       = mapped_column(Boolean, default=True)

    sizes: Mapped[list["PrintSize"]] = relationship(back_populates="print", cascade="all, delete-orphan")


class PrintSize(Base):
    __tablename__ = "print_sizes"

    id:       Mapped[int]     = mapped_column(primary_key=True)
    print_id: Mapped[int]     = mapped_column(ForeignKey("prints.id"))
    label:    Mapped[str]     = mapped_column(String(50))    # 5×5 см / 10×10 см ...
    price:    Mapped[Decimal] = mapped_column(Numeric(10, 2))

    print: Mapped["Print"] = relationship(back_populates="sizes")


# ── Готовый товар на складе ───────────────────────────────────────────────────

class ReadyProduct(Base):
    """
    Конкретная позиция на складе — изделие с уже нанесённой вышивкой.
    Цена финальная (включает и изделие и вышивку).
    """
    __tablename__ = "ready_products"

    id:              Mapped[int]        = mapped_column(primary_key=True)
    product_type_id: Mapped[int]        = mapped_column(ForeignKey("product_types.id"))
    color_id:        Mapped[int]        = mapped_column(ForeignKey("colors.id"))
    size_label:      Mapped[str]        = mapped_column(String(10))
    price:           Mapped[Decimal]    = mapped_column(Numeric(10, 2))  # финальная цена
    stock_quantity:  Mapped[int]        = mapped_column(Integer, default=0)
    image_url:       Mapped[str | None] = mapped_column(String(500))
    is_active:       Mapped[bool]       = mapped_column(Boolean, default=True)

    product_type: Mapped["ProductType"] = relationship(back_populates="ready_products")
    color:        Mapped["Color"]       = relationship()
    cart_items:   Mapped[list["CartItem"]]       = relationship(back_populates="ready_product")
    order_items:  Mapped[list["ReadyOrderItem"]] = relationship(back_populates="ready_product")