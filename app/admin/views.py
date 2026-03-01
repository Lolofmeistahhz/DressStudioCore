"""
app/admin/views.py
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
from app.models.constructor import CanvasTemplate, ConstructorOrder, ConstructorOrderStatus

logger = logging.getLogger(__name__)


class BaseModelView(ModelView):
    page_size = 20


class UserAdmin(BaseModelView):
    column_list = ["id", "telegram_id", "full_name", "username", "phone", "role", "created_at"]
    column_searchable_list = ["full_name", "username", "phone"]
    column_sortable_list = ["id", "created_at"]
    fields = [
        IntegerField("telegram_id",       label="Telegram ID"),
        StringField("username",           label="Username"),
        StringField("full_name",          label="ФИО"),
        StringField("phone",              label="Телефон"),
        EnumField("role",                 enum=UserRole,        label="Роль"),
        EnumField("delivery_carrier",     enum=DeliveryCarrier, label="Служба доставки", required=False),
        StringField("delivery_name",      label="Имя получателя"),
        StringField("delivery_city",      label="Город"),
        StringField("delivery_address",   label="Адрес"),
        DateTimeField("created_at",       label="Дата регистрации", read_only=True),
    ]
    def can_delete(self, request: Request) -> bool:
        return False


class ColorAdmin(BaseModelView):
    column_list = ["id", "name", "hex_code"]
    column_searchable_list = ["name"]
    fields = [
        StringField("name",     label="Название"),
        StringField("hex_code", label="HEX код (#RRGGBB)"),
    ]


class ProductTypeAdmin(BaseModelView):
    """
    image_url удалён из модели — изображения хранятся на уровне конкретных товаров.
    Остались: size_chart_url (таблица размеров) и color_palette_url (палитра цветов).
    """
    column_list = ["id", "name", "slug", "base_price", "is_active"]
    column_searchable_list = ["name", "slug"]
    fields = [
        StringField("name",              label="Название"),
        StringField("slug",              label="Слаг"),
        FloatField("base_price",         label="Базовая цена"),
        BooleanField("is_active",        label="Активен"),
        StringField("description",       label="Описание"),
        StringField("composition",       label="Состав ткани"),
        StringField("notes",             label="Примечания"),
        StringField("size_chart_url",    label="URL таблицы размеров"),
        StringField("color_palette_url", label="URL палитры цветов"),
        # image_url удалён
    ]


class ProductTypeSizeAdmin(BaseModelView):
    column_list = ["id", "product_type_id", "label", "length", "width", "sleeve", "shoulders", "waist_width"]
    column_searchable_list = ["label"]
    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        StringField("label",            label="Размер (XS/S/M/...)"),
        StringField("length",           label="Длина"),
        StringField("width",            label="Ширина"),
        StringField("sleeve",           label="Рукав"),
        StringField("shoulders",        label="Плечи"),
        StringField("waist_width",      label="Пояс (для свитшотов)"),
    ]


class ProductTypeColorAdmin(BaseModelView):
    column_list = ["id", "product_type_id", "color_id", "in_stock"]
    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        IntegerField("color_id",        label="ID цвета"),
        BooleanField("in_stock",        label="В наличии"),
    ]


class PrintAdmin(BaseModelView):
    column_list = ["id", "name", "is_active"]
    column_searchable_list = ["name"]
    fields = [
        StringField("name",      label="Название"),
        StringField("image_url", label="URL изображения"),
        BooleanField("is_active", label="Активен"),
    ]


class PrintSizeAdmin(BaseModelView):
    column_list = ["id", "print_id", "label", "price"]
    column_searchable_list = ["label"]
    fields = [
        IntegerField("print_id", label="ID принта"),
        StringField("label",     label="Размер (5×5 см / 10×10 см)"),
        FloatField("price",      label="Цена"),
    ]


class ReadyProductAdmin(BaseModelView):
    """
    name — название модели внутри типа (Базовая / Оверсайз / Цветочная и т.д.).
    Один тип может иметь несколько названий с разными цветами/размерами.
    """
    column_list = ["id", "product_type_id", "name", "color_id", "size_label", "price", "stock_quantity", "is_active"]
    column_searchable_list = ["name", "size_label"]
    column_sortable_list = ["product_type_id", "name", "price", "stock_quantity"]
    fields = [
        IntegerField("product_type_id", label="ID типа изделия"),
        StringField("name",             label="Название модели"),   # ← новое поле
        IntegerField("color_id",        label="ID цвета"),
        StringField("size_label",       label="Размер"),
        FloatField("price",             label="Цена"),
        IntegerField("stock_quantity",  label="Количество на складе"),
        StringField("image_url",        label="URL фото товара"),
        BooleanField("is_active",       label="Активен"),
    ]


class CartItemAdmin(BaseModelView):
    column_list = ["id", "user_id", "ready_product_id", "quantity", "added_at"]
    fields = [
        IntegerField("user_id",          label="ID пользователя"),
        IntegerField("ready_product_id", label="ID товара"),
        IntegerField("quantity",         label="Количество"),
        DateTimeField("added_at",        label="Добавлено", read_only=True),
    ]
    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderAdmin(BaseModelView):
    column_list = ["id", "user_id", "status", "total_price", "created_at"]
    column_sortable_list = ["created_at", "status"]
    fields = [
        IntegerField("user_id",          label="ID пользователя"),
        EnumField("status",              enum=ReadyOrderStatus,        label="Статус"),
        FloatField("total_price",        label="Сумма"),
        EnumField("carrier",             enum=OrderDeliveryCarrier,    label="Служба доставки"),
        StringField("delivery_name",     label="Имя получателя"),
        StringField("delivery_phone",    label="Телефон"),
        StringField("delivery_city",     label="Город"),
        StringField("delivery_address",  label="Адрес"),
        StringField("tracking_number",   label="Трекинг номер"),
        DateTimeField("created_at",      label="Создан", read_only=True),
    ]
    def can_create(self, request: Request) -> bool:
        return False


class ReadyOrderItemAdmin(BaseModelView):
    column_list = ["id", "order_id", "ready_product_id", "quantity", "price_fixed"]
    fields = [
        IntegerField("order_id",          label="ID заказа"),
        IntegerField("ready_product_id",  label="ID товара"),
        IntegerField("quantity",          label="Количество"),
        FloatField("price_fixed",         label="Цена на момент заказа"),
    ]
    def can_create(self, request: Request) -> bool:
        return False


class CustomOrderAdmin(BaseModelView):
    column_list = ["id", "user_id", "status", "product_type_id", "recommended_price", "final_price", "created_at"]
    column_sortable_list = ["created_at", "status"]
    fields = [
        IntegerField("user_id",            label="ID пользователя"),
        EnumField("status",                enum=CustomOrderStatus,     label="Статус"),
        IntegerField("product_type_id",    label="ID типа изделия"),
        IntegerField("color_id",           label="ID цвета"),
        StringField("size_label",          label="Размер"),
        IntegerField("print_id",           label="ID принта"),
        IntegerField("print_size_id",      label="ID размера принта"),
        # custom_images — JSON список URL, только для чтения в таблице
        StringField("comment",             label="Комментарий клиента"),
        StringField("admin_comment",       label="Комментарий админа"),
        FloatField("recommended_price",    label="Рекомендуемая цена"),
        FloatField("final_price",          label="Финальная цена"),
        EnumField("carrier",               enum=OrderDeliveryCarrier,  label="Служба доставки"),
        StringField("delivery_name",       label="Имя получателя"),
        StringField("delivery_phone",      label="Телефон"),
        StringField("delivery_city",       label="Город"),
        StringField("delivery_address",    label="Адрес"),
        DateTimeField("created_at",        label="Создан", read_only=True),
    ]
    def can_delete(self, request: Request) -> bool:
        return False


class PaymentAdmin(BaseModelView):
    column_list = ["id", "entity_type", "entity_id", "amount", "status", "created_at"]
    column_sortable_list = ["created_at", "status"]
    fields = [
        EnumField("entity_type",          enum=PaymentEntityType, label="Тип"),
        IntegerField("entity_id",         label="ID сущности"),
        FloatField("amount",              label="Сумма"),
        EnumField("status",               enum=PaymentStatus,     label="Статус"),
        StringField("yookassa_payment_id", label="Yookassa ID"),
        DateTimeField("created_at",       label="Создан", read_only=True),
    ]
    def can_create(self, request: Request) -> bool:
        return False


class CanvasTemplateAdmin(BaseModelView):
    column_list = ["id", "product_type_id", "color_id", "is_active"]
    fields = [
        IntegerField("product_type_id",   label="ID типа изделия"),
        IntegerField("color_id",          label="ID цвета"),
        StringField("canvas_image_url",   label="URL изображения"),
        BooleanField("is_active",         label="Активен"),
    ]


class ConstructorOrderAdmin(BaseModelView):
    column_list = ["id", "user_id", "canvas_template_id", "status", "final_price", "created_at"]
    column_sortable_list = ["created_at", "status"]
    fields = [
        IntegerField("user_id",             label="ID пользователя"),
        IntegerField("canvas_template_id",  label="ID шаблона"),
        FloatField("final_price",           label="Цена"),
        EnumField("status",                 enum=ConstructorOrderStatus, label="Статус"),
        StringField("admin_comment",        label="Комментарий"),
        StringField("delivery_name",        label="Имя получателя"),
        StringField("delivery_phone",       label="Телефон"),
        StringField("delivery_city",        label="Город"),
        StringField("delivery_address",     label="Адрес"),
        DateTimeField("created_at",         label="Создан", read_only=True),
    ]
    def can_create(self, request: Request) -> bool:
        return False