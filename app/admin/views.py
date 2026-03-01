"""
app/admin/views.py

Минимальная админка без сложных связей.
Только базовые поля + Enum для статусов.
"""
import logging
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.fields import (
    StringField, IntegerField, FloatField, BooleanField, EnumField, DateTimeField
)

from app.models.user import User, UserRole, DeliveryCarrier
from app.models.catalog import (
    Color, ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.models.order import (
    CartItem, ReadyOrder, ReadyOrderItem, CustomOrder,
    ReadyOrderStatus, CustomOrderStatus, DeliveryCarrier as OrderDeliveryCarrier,
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
    column_list = ["id", "telegram_id", "full_name", "username", "phone", "role", "created_at"]
    column_searchable_list = ["full_name", "username", "phone"]
    column_sortable_list = ["id", "created_at"]

    fields = [
        IntegerField("telegram_id", label="Telegram ID"),
        StringField("username", label="Username"),
        StringField("full_name", label="ФИО"),
        StringField("phone", label="Телефон"),
        EnumField("role", enum=UserRole, label="Роль"),
        EnumField("delivery_carrier", enum=DeliveryCarrier, label="Служба доставки", required=False),
        StringField("delivery_name", label="Имя получателя"),
        StringField("delivery_city", label="Город"),
        StringField("delivery_address", label="Адрес"),
        DateTimeField("created_at", label="Дата регистрации", read_only=True),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class ColorAdmin(BaseModelView):
    """Админка для цветов."""
    column_list = ["id", "name", "hex_code"]
    column_searchable_list = ["name"]

    fields = [
        StringField("name", label="Название"),
        StringField("hex_code", label="HEX код"),
    ]


class ProductTypeAdmin(BaseModelView):
    """Админка для типов продуктов."""
    column_list = ["id", "name", "slug", "base_price", "is_active"]
    column_searchable_list = ["name", "slug"]

    fields = [
        StringField("name", label="Название"),
        StringField("slug", label="Слаг"),
        FloatField("base_price", label="Базовая цена"),
        BooleanField("is_active", label="Активен"),
        StringField("description", label="Описание"),
        StringField("image_url", label="URL фото"),
        StringField("size_chart_url", label="URL таблицы размеров"),
        StringField("color_palette_url", label="URL палитры"),
    ]


class ProductTypeSizeAdmin(BaseModelView):
    """Админка для размеров продуктов."""
    column_list = ["id", "product_type_id", "label", "length", "width", "sleeve"]
    column_searchable_list = ["label"]

    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        StringField("label", label="Размер"),
        StringField("length", label="Длина"),
        StringField("width", label="Ширина"),
        StringField("sleeve", label="Рукав"),
    ]


class ProductTypeColorAdmin(BaseModelView):
    """Админка для цветов продуктов."""
    column_list = ["id", "product_type_id", "color_id", "in_stock"]

    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        IntegerField("color_id", label="ID цвета"),
        IntegerField("in_stock", label="В наличии"),
    ]


class PrintAdmin(BaseModelView):
    """Админка для принтов."""
    column_list = ["id", "name", "is_active"]
    column_searchable_list = ["name"]

    fields = [
        StringField("name", label="Название"),
        StringField("image_url", label="URL изображения"),
        BooleanField("is_active", label="Активен"),
    ]


class PrintSizeAdmin(BaseModelView):
    """Админка для размеров принтов."""
    column_list = ["id", "print_id", "label", "price"]
    column_searchable_list = ["label"]

    fields = [
        IntegerField("print_id", label="ID принта"),
        StringField("label", label="Размер"),
        FloatField("price", label="Цена"),
    ]


class ReadyProductAdmin(BaseModelView):
    """Админка для готовых продуктов."""
    column_list = ["id", "product_type_id", "color_id", "size_label", "price", "stock_quantity", "is_active"]
    column_searchable_list = ["size_label"]

    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        IntegerField("color_id", label="ID цвета"),
        StringField("size_label", label="Размер"),
        FloatField("price", label="Цена"),
        IntegerField("stock_quantity", label="Количество"),
        StringField("image_url", label="URL фото"),
        BooleanField("is_active", label="Активен"),
    ]


class CartItemAdmin(BaseModelView):
    """Админка для корзины."""
    column_list = ["id", "user_id", "ready_product_id", "quantity", "added_at"]

    fields = [
        IntegerField("user_id", label="ID пользователя"),
        IntegerField("ready_product_id", label="ID товара"),
        IntegerField("quantity", label="Количество"),
        DateTimeField("added_at", label="Добавлено", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderAdmin(BaseModelView):
    """Админка для готовых заказов."""
    column_list = ["id", "user_id", "status", "total_price", "created_at"]
    column_sortable_list = ["created_at", "status"]

    fields = [
        IntegerField("user_id", label="ID пользователя"),
        EnumField("status", enum=ReadyOrderStatus, label="Статус"),
        FloatField("total_price", label="Сумма"),
        EnumField("carrier", enum=OrderDeliveryCarrier, label="Служба доставки"),
        StringField("delivery_name", label="Имя получателя"),
        StringField("delivery_phone", label="Телефон"),
        StringField("delivery_city", label="Город"),
        StringField("delivery_address", label="Адрес"),
        StringField("tracking_number", label="Трекинг номер"),
        DateTimeField("created_at", label="Создан", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderItemAdmin(BaseModelView):
    """Админка для элементов готовых заказов."""
    column_list = ["id", "order_id", "ready_product_id", "quantity", "price_fixed"]

    fields = [
        IntegerField("order_id", label="ID заказа"),
        IntegerField("ready_product_id", label="ID товара"),
        IntegerField("quantity", label="Количество"),
        FloatField("price_fixed", label="Цена"),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class CustomOrderAdmin(BaseModelView):
    """Админка для кастомных заказов."""
    column_list = ["id", "user_id", "status", "product_type_id", "final_price", "created_at"]
    column_sortable_list = ["created_at", "status"]

    fields = [
        IntegerField("user_id", label="ID пользователя"),
        EnumField("status", enum=CustomOrderStatus, label="Статус"),
        IntegerField("product_type_id", label="ID типа изделия"),
        IntegerField("color_id", label="ID цвета"),
        StringField("size_label", label="Размер"),
        IntegerField("print_id", label="ID принта"),
        IntegerField("print_size_id", label="ID размера принта"),
        FloatField("recommended_price", label="Рекомендуемая цена"),
        FloatField("final_price", label="Финальная цена"),
        StringField("comment", label="Комментарий"),
        StringField("admin_comment", label="Комментарий админа"),
        EnumField("carrier", enum=OrderDeliveryCarrier, label="Служба доставки"),
        StringField("delivery_name", label="Имя получателя"),
        StringField("delivery_phone", label="Телефон"),
        StringField("delivery_city", label="Город"),
        StringField("delivery_address", label="Адрес"),
        DateTimeField("created_at", label="Создан", read_only=True),
    ]

    def can_delete(self, request: Request) -> bool:
        return False


class PaymentAdmin(BaseModelView):
    """Админка для платежей."""
    column_list = ["id", "entity_type", "entity_id", "amount", "status", "created_at"]
    column_sortable_list = ["created_at", "status"]

    fields = [
        EnumField("entity_type", enum=PaymentEntityType, label="Тип"),
        IntegerField("entity_id", label="ID сущности"),
        FloatField("amount", label="Сумма"),
        EnumField("status", enum=PaymentStatus, label="Статус"),
        StringField("yookassa_payment_id", label="Yookassa ID"),
        DateTimeField("created_at", label="Создан", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False


class CanvasTemplateAdmin(BaseModelView):
    """Админка для шаблонов канваса."""
    column_list = ["id", "product_type_id", "color_id", "is_active"]

    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        IntegerField("color_id", label="ID цвета"),
        StringField("canvas_image_url", label="URL изображения"),
        BooleanField("is_active", label="Активен"),
    ]


class ConstructorOrderAdmin(BaseModelView):
    """Админка для заказов конструктора."""
    column_list = ["id", "user_id", "canvas_template_id", "status", "final_price", "created_at"]
    column_sortable_list = ["created_at", "status"]

    fields = [
        IntegerField("user_id", label="ID пользователя"),
        IntegerField("canvas_template_id", label="ID шаблона"),
        FloatField("final_price", label="Цена"),
        EnumField("status", enum=ConstructorOrderStatus, label="Статус"),
        StringField("admin_comment", label="Комментарий"),
        StringField("delivery_name", label="Имя получателя"),
        StringField("delivery_phone", label="Телефон"),
        StringField("delivery_city", label="Город"),
        StringField("delivery_address", label="Адрес"),
        DateTimeField("created_at", label="Создан", read_only=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False