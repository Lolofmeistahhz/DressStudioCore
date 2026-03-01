"""
app/admin/views.py

Обновлённая админка с улучшенным UX:
- Enum поля отображаются выпадающими списками (EnumField)
- Внешние ключи — удобные выпадающие списки (RelationField)
- Добавлены все пропущенные поля моделей
- JSON поля пока как TextAreaField (требуют ручного ввода JSON)
- Даты readonly
"""

import uuid
import logging
from pathlib import Path
from typing import Any, Dict

from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import (
    StringField, IntegerField, FloatField, BooleanField,
    EnumField, RelationField, TextAreaField, DateTimeField, URLField,
)

from app.core.config import settings
from app.models.user import User, UserRole, DeliveryCarrier as UserDeliveryCarrier
from app.models.catalog import (
    Color, ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.models.order import (
    CartItem, ReadyOrder, ReadyOrderItem, CustomOrder,
    ReadyOrderStatus, CustomOrderStatus, DeliveryCarrier as OrderDeliveryCarrier,
)
from app.models.payment import Payment, PaymentEntityType, PaymentStatus
from app.models.constructor import CanvasTemplate, ConstructorOrder, ConstructorOrderStatus

logger = logging.getLogger(__name__)


class BaseModelView(ModelView):
    """Базовый класс для всех представлений админки."""
    pass


class UserAdmin(BaseModelView):
    """Пользователи."""

    page_size = 20
    column_list = [
        User.id, User.telegram_id, User.full_name, User.username,
        User.phone, User.role, User.delivery_carrier, User.created_at,
    ]
    column_searchable_list = [User.full_name, User.username, User.phone, User.telegram_id]
    column_sortable_list = [User.id, User.created_at, User.role]

    fields = [
        IntegerField('telegram_id'),
        StringField('full_name'),
        StringField('username'),
        StringField('phone'),
        EnumField('role', enum=UserRole),
        EnumField('delivery_carrier', enum=UserDeliveryCarrier),
        StringField('delivery_name'),
        StringField('delivery_city'),
        StringField('delivery_address'),
        DateTimeField('created_at', read_only=True),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class ColorAdmin(BaseModelView):
    """Цвета."""

    column_list = [Color.id, Color.name, Color.hex_code]
    column_searchable_list = [Color.name]
    column_sortable_list = [Color.id, Color.name]

    fields = [
        StringField('name'),
        StringField('hex_code'),
    ]


class ProductTypeAdmin(BaseModelView):
    """Типы изделий."""

    column_list = [
        ProductType.id, ProductType.name, ProductType.slug,
        ProductType.base_price, ProductType.is_active,
        ProductType.image_url, ProductType.size_chart_url,
    ]
    column_searchable_list = [ProductType.name, ProductType.slug]
    column_sortable_list = [ProductType.base_price, ProductType.is_active]

    fields = [
        StringField('name'),
        StringField('slug'),
        FloatField('base_price'),
        BooleanField('is_active'),
        URLField('image_url'),
        URLField('size_chart_url'),
        URLField('color_palette_url'),
        TextAreaField('description'),
        StringField('composition'),
        TextAreaField('notes'),
    ]


class ProductTypeSizeAdmin(BaseModelView):
    """Размеры типов изделий."""

    column_list = [
        ProductTypeSize.id, ProductTypeSize.product_type_id,
        ProductTypeSize.label, ProductTypeSize.length,
        ProductTypeSize.width, ProductTypeSize.sleeve,
        ProductTypeSize.shoulders, ProductTypeSize.waist_width,
    ]
    column_searchable_list = [ProductTypeSize.label]

    fields = [
        RelationField('product_type_id', identity='producttype'),
        StringField('label'),
        StringField('length'),
        StringField('width'),
        StringField('sleeve'),
        StringField('shoulders'),
        StringField('waist_width'),
    ]


class ProductTypeColorAdmin(BaseModelView):
    """Цвета, доступные для типа изделия."""

    column_list = [
        ProductTypeColor.id, ProductTypeColor.product_type_id,
        ProductTypeColor.color_id, ProductTypeColor.in_stock,
    ]

    fields = [
        RelationField('product_type_id', identity='producttype'),
        RelationField('color_id', identity='color'),
        BooleanField('in_stock'),
    ]


class PrintAdmin(BaseModelView):
    """Принты / вышивки."""

    column_list = [Print.id, Print.name, Print.image_url, Print.is_active]
    column_searchable_list = [Print.name]

    fields = [
        StringField('name'),
        BooleanField('is_active'),
        URLField('image_url'),
    ]


class PrintSizeAdmin(BaseModelView):
    """Размеры принтов."""

    column_list = [
        PrintSize.id, PrintSize.print_id,
        PrintSize.label, PrintSize.price,
    ]
    column_searchable_list = [PrintSize.label]

    fields = [
        RelationField('print_id', identity='print'),
        StringField('label'),
        FloatField('price'),
    ]


class ReadyProductAdmin(BaseModelView):
    """Готовые товары на складе."""

    column_list = [
        ReadyProduct.id, ReadyProduct.product_type_id,
        ReadyProduct.color_id, ReadyProduct.size_label,
        ReadyProduct.price, ReadyProduct.stock_quantity,
        ReadyProduct.is_active, ReadyProduct.image_url,
    ]
    column_sortable_list = [ReadyProduct.price, ReadyProduct.stock_quantity]
    column_searchable_list = [ReadyProduct.size_label]

    fields = [
        RelationField('product_type_id', identity='producttype'),
        RelationField('color_id', identity='color'),
        StringField('size_label'),
        FloatField('price'),
        IntegerField('stock_quantity'),
        BooleanField('is_active'),
        URLField('image_url'),
    ]


class CartItemAdmin(BaseModelView):
    """Элементы корзины."""

    column_list = [
        CartItem.id, CartItem.user_id,
        CartItem.ready_product_id, CartItem.quantity, CartItem.added_at,
    ]

    fields = [
        RelationField('user_id', identity='user'),
        RelationField('ready_product_id', identity='readyproduct'),
        IntegerField('quantity'),
        DateTimeField('added_at', read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderAdmin(BaseModelView):
    """Заказы готовых товаров."""

    page_size = 20
    column_list = [
        ReadyOrder.id, ReadyOrder.user_id, ReadyOrder.status,
        ReadyOrder.total_price, ReadyOrder.carrier,
        ReadyOrder.delivery_city, ReadyOrder.tracking_number,
        ReadyOrder.created_at,
    ]
    column_sortable_list = [ReadyOrder.created_at, ReadyOrder.status]

    fields = [
        RelationField('user_id', identity='user'),
        EnumField('status', enum=ReadyOrderStatus),
        FloatField('total_price'),
        EnumField('carrier', enum=OrderDeliveryCarrier),
        StringField('delivery_name'),
        StringField('delivery_phone'),
        StringField('delivery_city'),
        StringField('delivery_address'),
        StringField('tracking_number'),
        DateTimeField('created_at', read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderItemAdmin(BaseModelView):
    """Позиции заказов готовых товаров."""

    column_list = [
        ReadyOrderItem.id, ReadyOrderItem.order_id,
        ReadyOrderItem.ready_product_id, ReadyOrderItem.quantity,
        ReadyOrderItem.price_fixed,
    ]

    fields = [
        RelationField('order_id', identity='readyorder'),
        RelationField('ready_product_id', identity='readyproduct'),
        IntegerField('quantity'),
        FloatField('price_fixed'),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CustomOrderAdmin(BaseModelView):
    """Кастомные заказы (с вышивкой)."""

    page_size = 20
    column_list = [
        CustomOrder.id, CustomOrder.user_id, CustomOrder.status,
        CustomOrder.product_type_id, CustomOrder.size_label,
        CustomOrder.recommended_price, CustomOrder.final_price,
        CustomOrder.created_at,
    ]
    column_sortable_list = [CustomOrder.created_at, CustomOrder.status]

    fields = [
        RelationField('user_id', identity='user'),
        RelationField('product_type_id', identity='producttype'),
        RelationField('color_id', identity='color'),
        StringField('size_label'),
        RelationField('print_id', identity='print'),
        RelationField('print_size_id', identity='printsize'),
        # JSON поле — пока как текст (вводить в виде JSON)
        TextAreaField('custom_images'),
        TextAreaField('comment'),
        FloatField('recommended_price'),
        FloatField('final_price'),
        EnumField('status', enum=CustomOrderStatus),
        TextAreaField('admin_comment'),
        EnumField('carrier', enum=OrderDeliveryCarrier),
        StringField('delivery_name'),
        StringField('delivery_phone'),
        StringField('delivery_city'),
        StringField('delivery_address'),
        DateTimeField('created_at', read_only=True),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class PaymentAdmin(BaseModelView):
    """Платежи."""

    page_size = 20
    column_list = [
        Payment.id, Payment.entity_type, Payment.entity_id,
        Payment.amount, Payment.status,
        Payment.yookassa_payment_id, Payment.created_at,
    ]
    column_sortable_list = [Payment.created_at, Payment.status]

    fields = [
        EnumField('entity_type', enum=PaymentEntityType),
        IntegerField('entity_id'),
        FloatField('amount'),
        EnumField('status', enum=PaymentStatus),
        StringField('yookassa_payment_id'),
        DateTimeField('created_at', read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CanvasTemplateAdmin(BaseModelView):
    """Шаблоны для конструктора."""

    column_list = [
        CanvasTemplate.id, CanvasTemplate.product_type_id,
        CanvasTemplate.color_id, CanvasTemplate.canvas_image_url,
        CanvasTemplate.is_active,
    ]

    fields = [
        RelationField('product_type_id', identity='producttype'),
        RelationField('color_id', identity='color'),
        BooleanField('is_active'),
        URLField('canvas_image_url'),
        IntegerField('width_px'),
        IntegerField('height_px'),
        FloatField('width_cm'),
        FloatField('height_cm'),
        TextAreaField('embroidery_zones'),  # JSON
    ]


class ConstructorOrderAdmin(BaseModelView):
    """Заказы из конструктора."""

    column_list = [
        ConstructorOrder.id, ConstructorOrder.user_id,
        ConstructorOrder.status, ConstructorOrder.final_price,
        ConstructorOrder.created_at,
    ]

    fields = [
        RelationField('user_id', identity='user'),
        RelationField('canvas_template_id', identity='canvastemplate'),
        TextAreaField('placements'),  # JSON
        URLField('snapshot_url'),
        FloatField('recommended_price'),
        FloatField('final_price'),
        EnumField('status', enum=ConstructorOrderStatus),
        TextAreaField('admin_comment'),
        EnumField('carrier', enum=OrderDeliveryCarrier),
        StringField('delivery_name'),
        StringField('delivery_phone'),
        StringField('delivery_city'),
        StringField('delivery_address'),
        DateTimeField('created_at', read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False