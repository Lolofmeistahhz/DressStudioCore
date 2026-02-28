"""
app/admin/views.py

Админка с загрузкой файлов через отдельный эндпоинт.
"""
import uuid
import logging
from pathlib import Path
from typing import Any, Dict

from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import StringField, IntegerField, FloatField, BooleanField

from app.core.config import settings
from app.models.user import User
from app.models.catalog import (
    Color, ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.models.order import (
    CartItem, ReadyOrder, ReadyOrderItem, CustomOrder,
)
from app.models.payment import Payment
from app.models.constructor import CanvasTemplate, ConstructorOrder

logger = logging.getLogger(__name__)


class BaseModelView(ModelView):
    """Базовый класс для всех представлений админки."""
    pass


class UserAdmin(BaseModelView):
    """Админка для пользователей."""

    page_size = 20
    column_list = [
        User.id, User.full_name, User.username, User.phone,
        User.delivery_carrier, User.delivery_city, User.created_at,
    ]
    column_searchable_list = [User.full_name, User.username, User.phone]
    column_sortable_list = [User.id, User.created_at]

    fields = [
        StringField('full_name'),
        StringField('username'),
        StringField('phone'),
        StringField('delivery_carrier'),
        StringField('delivery_city'),
        StringField('delivery_address'),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class ColorAdmin(BaseModelView):
    """Админка для цветов."""

    column_list = [Color.id, Color.name, Color.hex_code, Color.palette_image_url]
    column_searchable_list = [Color.name]
    column_sortable_list = [Color.id, Color.name]

    fields = [
        StringField('name'),
        StringField('hex_code'),
        StringField('palette_image_url'),  # было FileField
    ]


class ProductTypeAdmin(BaseModelView):
    """Админка для типов продуктов."""

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
        StringField('image_url'),          # было FileField
        StringField('size_chart_url'),     # было FileField
        StringField('description'),
        StringField('composition'),
        StringField('notes'),
    ]


class ProductTypeSizeAdmin(BaseModelView):
    """Админка для размеров продуктов."""

    column_list = [
        ProductTypeSize.id, ProductTypeSize.product_type_id,
        ProductTypeSize.label, ProductTypeSize.length,
        ProductTypeSize.width, ProductTypeSize.sleeve,
    ]
    column_searchable_list = [ProductTypeSize.label]

    fields = [
        IntegerField('product_type_id'),
        StringField('label'),
        FloatField('length'),
        FloatField('width'),
        FloatField('sleeve'),
    ]


class ProductTypeColorAdmin(BaseModelView):
    """Админка для цветов продуктов."""

    column_list = [
        ProductTypeColor.id, ProductTypeColor.product_type_id,
        ProductTypeColor.color_id, ProductTypeColor.in_stock,
    ]

    fields = [
        IntegerField('product_type_id'),
        IntegerField('color_id'),
        IntegerField('in_stock'),
    ]


class PrintAdmin(BaseModelView):
    """Админка для принтов."""

    column_list = [Print.id, Print.name, Print.image_url, Print.is_active]
    column_searchable_list = [Print.name]

    fields = [
        StringField('name'),
        BooleanField('is_active'),
        StringField('image_url'),  # было FileField
    ]


class PrintSizeAdmin(BaseModelView):
    """Админка для размеров принтов."""

    column_list = [
        PrintSize.id, PrintSize.print_id,
        PrintSize.label, PrintSize.price,
    ]
    column_searchable_list = [PrintSize.label]

    fields = [
        IntegerField('print_id'),
        StringField('label'),
        FloatField('price'),
    ]


class ReadyProductAdmin(BaseModelView):
    """Админка для готовых продуктов."""

    column_list = [
        ReadyProduct.id, ReadyProduct.product_type_id,
        ReadyProduct.color_id, ReadyProduct.size_label,
        ReadyProduct.price, ReadyProduct.stock_quantity,
        ReadyProduct.is_active, ReadyProduct.image_url,
    ]
    column_sortable_list = [ReadyProduct.price, ReadyProduct.stock_quantity]
    column_searchable_list = [ReadyProduct.size_label]

    fields = [
        IntegerField('product_type_id'),
        IntegerField('color_id'),
        StringField('size_label'),
        FloatField('price'),
        IntegerField('stock_quantity'),
        BooleanField('is_active'),
        StringField('image_url'),  # было FileField
    ]


class CartItemAdmin(BaseModelView):
    """Админка для корзины."""

    column_list = [
        CartItem.id, CartItem.user_id,
        CartItem.ready_product_id, CartItem.quantity, CartItem.added_at,
    ]

    fields = [
        IntegerField('user_id'),
        IntegerField('ready_product_id'),
        IntegerField('quantity'),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderAdmin(BaseModelView):
    """Админка для готовых заказов."""

    page_size = 20
    column_list = [
        ReadyOrder.id, ReadyOrder.user_id, ReadyOrder.status,
        ReadyOrder.total_price, ReadyOrder.carrier,
        ReadyOrder.delivery_city, ReadyOrder.tracking_number, ReadyOrder.created_at,
    ]
    column_sortable_list = [ReadyOrder.created_at, ReadyOrder.status]

    fields = [
        IntegerField('user_id'),
        StringField('status'),
        FloatField('total_price'),
        StringField('carrier'),
        StringField('delivery_city'),
        StringField('tracking_number'),
        StringField('delivery_address'),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderItemAdmin(BaseModelView):
    """Админка для элементов готовых заказов."""

    column_list = [
        ReadyOrderItem.id, ReadyOrderItem.order_id,
        ReadyOrderItem.ready_product_id, ReadyOrderItem.quantity,
        ReadyOrderItem.price_fixed,
    ]

    fields = [
        IntegerField('order_id'),
        IntegerField('ready_product_id'),
        IntegerField('quantity'),
        FloatField('price_fixed'),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CustomOrderAdmin(BaseModelView):
    """Админка для кастомных заказов."""

    page_size = 20
    column_list = [
        CustomOrder.id, CustomOrder.user_id, CustomOrder.status,
        CustomOrder.product_type_id, CustomOrder.size_label,
        CustomOrder.recommended_price, CustomOrder.final_price,
        CustomOrder.created_at,
    ]
    column_sortable_list = [CustomOrder.created_at, CustomOrder.status]

    fields = [
        IntegerField('user_id'),
        StringField('status'),
        IntegerField('product_type_id'),
        StringField('size_label'),
        FloatField('recommended_price'),
        FloatField('final_price'),
        StringField('user_comment'),
        StringField('admin_comment'),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class PaymentAdmin(BaseModelView):
    """Админка для платежей."""

    page_size = 20
    column_list = [
        Payment.id, Payment.entity_type, Payment.entity_id,
        Payment.amount, Payment.status,
        Payment.yookassa_payment_id, Payment.created_at,
    ]
    column_sortable_list = [Payment.created_at, Payment.status]

    fields = [
        StringField('entity_type'),
        IntegerField('entity_id'),
        FloatField('amount'),
        StringField('status'),
        StringField('yookassa_payment_id'),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CanvasTemplateAdmin(BaseModelView):
    """Админка для шаблонов канваса."""

    column_list = [
        CanvasTemplate.id, CanvasTemplate.product_type_id,
        CanvasTemplate.color_id, CanvasTemplate.canvas_image_url,
        CanvasTemplate.is_active,
    ]

    fields = [
        IntegerField('product_type_id'),
        IntegerField('color_id'),
        BooleanField('is_active'),
        StringField('canvas_image_url'),  # было FileField
        StringField('template_data'),
    ]


class ConstructorOrderAdmin(BaseModelView):
    """Админка для заказов конструктора."""

    column_list = [
        ConstructorOrder.id, ConstructorOrder.user_id,
        ConstructorOrder.status, ConstructorOrder.final_price,
        ConstructorOrder.created_at,
    ]
    fields = [
        IntegerField('user_id'),
        StringField('status'),
        FloatField('final_price'),
        StringField('design_data'),
    ]

    def can_create(self, request: Request) -> bool:
        return False