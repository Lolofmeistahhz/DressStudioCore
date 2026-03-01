"""
app/admin/views.py

Админка с улучшенным UX: enum, связи, предпросмотр изображений.
Исправлена проблема с joined loader для связанных полей в списках.
"""
import uuid
import logging
from pathlib import Path
from typing import Any, Dict

from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import (
    StringField, IntegerField, FloatField, BooleanField,
    EnumField, RelationField, ImageField, TextAreaField,
    JSONField, DateTimeField
)
from starlette_admin.helpers import prettify_class_name

from app.core.config import settings
from app.models.user import User, UserRole, DeliveryCarrier
from app.models.catalog import (
    Color, ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.models.order import (
    CartItem, ReadyOrder, ReadyOrderStatus, ReadyOrderItem,
    CustomOrder, CustomOrderStatus, DeliveryCarrier as OrderDeliveryCarrier,
)
from app.models.payment import Payment, PaymentEntityType, PaymentStatus
from app.models.constructor import (
    CanvasTemplate, ConstructorOrder, ConstructorOrderStatus
)

logger = logging.getLogger(__name__)

class BaseModelView(ModelView):
    """Базовый класс для всех представлений админки."""
    page_size = 20


class UserAdmin(BaseModelView):
    """Админка для пользователей."""

    column_list = [
        User.id, "full_name", "username", "phone", "role",
        "delivery_carrier", "delivery_city", "created_at"
    ]
    column_searchable_list = [User.full_name, User.username, User.phone]
    column_sortable_list = [User.id, User.created_at, User.role]
    column_filters = [User.role, User.delivery_carrier]

    fields = [
        StringField("full_name"),
        StringField("username"),
        StringField("phone"),
        EnumField("role", enum=UserRole),
        EnumField("delivery_carrier", enum=DeliveryCarrier, required=False),
        StringField("delivery_city"),
        StringField("delivery_address"),
        StringField("delivery_name"),
        DateTimeField("created_at", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class ColorAdmin(BaseModelView):
    """Админка для цветов."""

    column_list = ["id", "name", "hex_code", "palette_image_url"]
    column_searchable_list = ["name"]
    column_sortable_list = ["id", "name"]
    column_formatters = {
        "palette_image_url": lambda obj, prop: f'<img src="{obj.palette_image_url}" height="40">' if obj.palette_image_url else ''
    }

    fields = [
        StringField("name"),
        StringField("hex_code"),
        ImageField("palette_image_url"),
    ]


class ProductTypeAdmin(BaseModelView):
    """Админка для типов продуктов."""

    column_list = [
        "id", "name", "slug", "base_price", "is_active",
        "image_url", "size_chart_url", "color_palette_url"
    ]
    column_searchable_list = ["name", "slug"]
    column_sortable_list = ["base_price", "is_active"]
    column_filters = ["is_active"]
    column_formatters = {
        "image_url": lambda obj, prop: f'<img src="{obj.image_url}" height="40">' if obj.image_url else '',
        "size_chart_url": lambda obj, prop: f'<a href="{obj.size_chart_url}" target="_blank">📄</a>' if obj.size_chart_url else '',
        "color_palette_url": lambda obj, prop: f'<img src="{obj.color_palette_url}" height="40">' if obj.color_palette_url else '',
    }

    fields = [
        StringField("name"),
        StringField("slug"),
        FloatField("base_price"),
        BooleanField("is_active"),
        ImageField("image_url", label="Фото изделия"),
        ImageField("size_chart_url", label="Таблица размеров"),
        ImageField("color_palette_url", label="Палитра цветов"),
        TextAreaField("description"),
        StringField("composition"),
        TextAreaField("notes"),
    ]


class ProductTypeSizeAdmin(BaseModelView):
    """Админка для размеров продуктов."""

    column_list = [
        "id", "product_type_id", "label", "length", "width", "sleeve", "shoulders", "waist_width"
    ]
    column_labels = {
        "product_type_id": "Product Type"
    }
    column_formatters = {
        "product_type_id": lambda obj, prop: obj.product_type.name if obj.product_type else ""
    }
    column_searchable_list = ["label"]
    column_sortable_list = ["product_type_id", "label"]
    column_filters = ["product_type_id"]

    fields = [
        RelationField("product_type_id", identity="product_type", label="Тип изделия"),
        StringField("label"),
        StringField("length"),
        StringField("width"),
        StringField("sleeve"),
        StringField("shoulders"),
        StringField("waist_width"),
    ]


class ProductTypeColorAdmin(BaseModelView):
    """Админка для цветов продуктов."""

    column_list = [
        "id", "product_type_id", "color_id", "in_stock"
    ]
    column_labels = {
        "product_type_id": "Product Type",
        "color_id": "Color"
    }
    column_formatters = {
        "product_type_id": lambda obj, prop: obj.product_type.name if obj.product_type else "",
        "color_id": lambda obj, prop: obj.color.name if obj.color else ""
    }
    column_sortable_list = ["product_type_id", "color_id"]
    column_filters = ["in_stock"]

    fields = [
        RelationField("product_type_id", identity="product_type", label="Тип изделия"),
        RelationField("color_id", identity="color", label="Цвет"),
        BooleanField("in_stock"),
    ]


class PrintAdmin(BaseModelView):
    """Админка для принтов."""

    column_list = ["id", "name", "image_url", "is_active"]
    column_searchable_list = ["name"]
    column_filters = ["is_active"]
    column_formatters = {
        "image_url": lambda obj, prop: f'<img src="{obj.image_url}" height="40">' if obj.image_url else ''
    }

    fields = [
        StringField("name"),
        BooleanField("is_active"),
        ImageField("image_url"),
    ]


class PrintSizeAdmin(BaseModelView):
    """Админка для размеров принтов."""

    column_list = [
        "id", "print_id", "label", "price"
    ]
    column_labels = {
        "print_id": "Print"
    }
    column_formatters = {
        "print_id": lambda obj, prop: obj.print.name if obj.print else ""
    }
    column_searchable_list = ["label"]
    column_sortable_list = ["print_id", "price"]

    fields = [
        RelationField("print_id", identity="print", label="Принт"),
        StringField("label"),
        FloatField("price"),
    ]


class ReadyProductAdmin(BaseModelView):
    """Админка для готовых продуктов."""

    column_list = [
        "id", "product_type_id", "color_id", "size_label",
        "price", "stock_quantity", "is_active", "image_url"
    ]
    column_labels = {
        "product_type_id": "Product Type",
        "color_id": "Color"
    }
    column_formatters = {
        "product_type_id": lambda obj, prop: obj.product_type.name if obj.product_type else "",
        "color_id": lambda obj, prop: obj.color.name if obj.color else "",
        "image_url": lambda obj, prop: f'<img src="{obj.image_url}" height="40">' if obj.image_url else ''
    }
    column_searchable_list = ["size_label"]
    column_sortable_list = ["price", "stock_quantity"]
    column_filters = ["is_active", "product_type_id", "color_id"]

    fields = [
        RelationField("product_type_id", identity="product_type", label="Тип изделия"),
        RelationField("color_id", identity="color", label="Цвет"),
        StringField("size_label"),
        FloatField("price"),
        IntegerField("stock_quantity"),
        BooleanField("is_active"),
        ImageField("image_url"),
    ]


class CartItemAdmin(BaseModelView):
    """Админка для корзины."""

    column_list = [
        "id", "user_id", "ready_product_id", "quantity", "added_at"
    ]
    column_labels = {
        "user_id": "User",
        "ready_product_id": "Ready Product"
    }
    column_formatters = {
        "user_id": lambda obj, prop: obj.user.full_name if obj.user else "",
        "ready_product_id": lambda obj, prop: f"{obj.ready_product.product_type.name} / {obj.ready_product.color.name} / {obj.ready_product.size_label}" if obj.ready_product else ""
    }
    column_sortable_list = ["added_at"]

    fields = [
        RelationField("user_id", identity="user", label="Пользователь"),
        RelationField("ready_product_id", identity="ready_product", label="Товар"),
        IntegerField("quantity"),
        DateTimeField("added_at", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class ReadyOrderAdmin(BaseModelView):
    """Админка для готовых заказов."""

    page_size = 20
    column_list = [
        "id", "user_id", "status", "total_price", "carrier",
        "delivery_city", "tracking_number", "created_at"
    ]
    column_labels = {
        "user_id": "User"
    }
    column_formatters = {
        "user_id": lambda obj, prop: obj.user.full_name if obj.user else ""
    }
    column_sortable_list = ["created_at", "status", "total_price"]
    column_searchable_list = ["user.full_name", "tracking_number"]  # Поиск по связанному полю оставляем, но возможно тоже надо изменить. Пока оставим.
    column_filters = ["status", "carrier"]

    fields = [
        RelationField("user_id", identity="user", label="Пользователь"),
        EnumField("status", enum=ReadyOrderStatus),
        FloatField("total_price", read_only=True),
        EnumField("carrier", enum=OrderDeliveryCarrier),
        StringField("delivery_name"),
        StringField("delivery_phone"),
        StringField("delivery_city"),
        StringField("delivery_address"),
        StringField("tracking_number"),
        DateTimeField("created_at", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class ReadyOrderItemAdmin(BaseModelView):
    """Админка для элементов готовых заказов."""

    column_list = [
        "id", "order_id", "ready_product_id", "quantity", "price_fixed"
    ]
    column_labels = {
        "order_id": "Order",
        "ready_product_id": "Ready Product"
    }
    column_formatters = {
        "order_id": lambda obj, prop: f"Order #{obj.order_id}",
        "ready_product_id": lambda obj, prop: f"{obj.ready_product.product_type.name} / {obj.ready_product.color.name} / {obj.ready_product.size_label}" if obj.ready_product else ""
    }

    fields = [
        RelationField("order_id", identity="ready_order", label="Заказ"),
        RelationField("ready_product_id", identity="ready_product", label="Товар"),
        IntegerField("quantity"),
        FloatField("price_fixed"),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CustomOrderAdmin(BaseModelView):
    """Админка для кастомных заказов."""

    page_size = 20
    column_list = [
        "id", "user_id", "status", "product_type_id", "color_id",
        "size_label", "recommended_price", "final_price", "created_at"
    ]
    column_labels = {
        "user_id": "User",
        "product_type_id": "Product Type",
        "color_id": "Color"
    }
    column_formatters = {
        "user_id": lambda obj, prop: obj.user.full_name if obj.user else "",
        "product_type_id": lambda obj, prop: obj.product_type.name if obj.product_type else "",
        "color_id": lambda obj, prop: obj.color.name if obj.color else ""
    }
    column_sortable_list = ["created_at", "status"]
    column_searchable_list = ["user.full_name", "admin_comment"]
    column_filters = ["status", "product_type_id", "color_id"]

    fields = [
        RelationField("user_id", identity="user", label="Пользователь"),
        EnumField("status", enum=CustomOrderStatus),
        RelationField("product_type_id", identity="product_type", label="Тип изделия"),
        RelationField("color_id", identity="color", label="Цвет"),
        StringField("size_label"),
        RelationField("print_id", identity="print", label="Принт (каталог)", required=False),
        RelationField("print_size_id", identity="print_size", label="Размер принта", required=False),
        JSONField("custom_images", label="Свои изображения (массив URL)"),
        TextAreaField("comment", label="Комментарий клиента"),
        FloatField("recommended_price", read_only=True),
        FloatField("final_price"),
        TextAreaField("admin_comment"),
        EnumField("carrier", enum=OrderDeliveryCarrier),
        StringField("delivery_name"),
        StringField("delivery_phone"),
        StringField("delivery_city"),
        StringField("delivery_address"),
        DateTimeField("created_at", read_only=True),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class PaymentAdmin(BaseModelView):
    """Админка для платежей."""

    page_size = 20
    column_list = [
        "id", "entity_type", "entity_id", "amount", "status",
        "yookassa_payment_id", "created_at"
    ]
    column_sortable_list = ["created_at", "status"]
    column_filters = ["entity_type", "status"]

    fields = [
        EnumField("entity_type", enum=PaymentEntityType),
        IntegerField("entity_id"),
        FloatField("amount"),
        EnumField("status", enum=PaymentStatus),
        StringField("yookassa_payment_id"),
        DateTimeField("created_at", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class CanvasTemplateAdmin(BaseModelView):
    """Админка для шаблонов канваса."""

    column_list = [
        "id", "product_type_id", "color_id", "canvas_image_url", "is_active"
    ]
    column_labels = {
        "product_type_id": "Product Type",
        "color_id": "Color"
    }
    column_formatters = {
        "product_type_id": lambda obj, prop: obj.product_type.name if obj.product_type else "",
        "color_id": lambda obj, prop: obj.color.name if obj.color else "",
        "canvas_image_url": lambda obj, prop: f'<img src="{obj.canvas_image_url}" height="40">' if obj.canvas_image_url else ''
    }
    column_filters = ["is_active", "product_type_id", "color_id"]

    fields = [
        RelationField("product_type_id", identity="product_type", label="Тип изделия"),
        RelationField("color_id", identity="color", label="Цвет"),
        ImageField("canvas_image_url", label="Изображение канваса"),
        IntegerField("width_px"),
        IntegerField("height_px"),
        FloatField("width_cm"),
        FloatField("height_cm"),
        JSONField("embroidery_zones", label="Зоны вышивки"),
        BooleanField("is_active"),
    ]


class ConstructorOrderAdmin(BaseModelView):
    """Админка для заказов конструктора."""

    column_list = [
        "id", "user_id", "canvas_template_id", "status", "final_price", "created_at"
    ]
    column_labels = {
        "user_id": "User",
        "canvas_template_id": "Canvas Template"
    }
    column_formatters = {
        "user_id": lambda obj, prop: obj.user.full_name if obj.user else "",
        "canvas_template_id": lambda obj, prop: f"{obj.canvas_template.product_type.name} / {obj.canvas_template.color.name}" if obj.canvas_template else "",
        "snapshot_url": lambda obj, prop: f'<img src="{obj.snapshot_url}" height="40">' if obj.snapshot_url else ''
    }
    column_sortable_list = ["created_at", "status"]
    column_filters = ["status"]

    fields = [
        RelationField("user_id", identity="user", label="Пользователь"),
        RelationField("canvas_template_id", identity="canvas_template", label="Шаблон"),
        JSONField("placements", label="Размещения принтов"),
        ImageField("snapshot_url", label="Превью"),
        FloatField("recommended_price", read_only=True),
        FloatField("final_price"),
        EnumField("status", enum=ConstructorOrderStatus),
        TextAreaField("admin_comment"),
        StringField("carrier"),
        StringField("delivery_name"),
        StringField("delivery_phone"),
        StringField("delivery_city"),
        StringField("delivery_address"),
        DateTimeField("created_at", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False