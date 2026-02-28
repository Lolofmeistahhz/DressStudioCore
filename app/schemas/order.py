from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator


# ── Ready Order ────────────────────────────────────────────────────────────────

class ReadyOrderItemOut(BaseModel):
    id: int
    ready_product_id: int
    quantity: int
    price_fixed: Decimal

    model_config = {"from_attributes": True}


class ReadyOrderOut(BaseModel):
    id: int
    status: str
    total_price: Decimal
    carrier: str
    delivery_name: str
    delivery_phone: str
    delivery_city: str
    delivery_address: str
    tracking_number: Optional[str]
    created_at: datetime
    items: list[ReadyOrderItemOut]

    model_config = {"from_attributes": True}


# ── Custom Order ───────────────────────────────────────────────────────────────

class CustomOrderCreate(BaseModel):
    product_type_id: int
    color_id: int
    size_label: str

    # Вышивка — один из двух вариантов
    print_id: Optional[int] = None
    print_size_id: Optional[int] = None
    custom_images: Optional[list[str]] = None   # список URL загруженных фото
    comment: Optional[str] = None

    @model_validator(mode="after")
    def check_embroidery(self):
        has_catalog = self.print_id is not None
        has_custom = bool(self.custom_images)

        if not has_catalog and not has_custom:
            raise ValueError(
                "Укажите принт из каталога (print_id + print_size_id) "
                "или загрузите своё фото (custom_images)"
            )
        if has_catalog and has_custom:
            raise ValueError(
                "Выберите либо принт из каталога, либо своё фото — не оба варианта"
            )
        if has_catalog and not self.print_size_id:
            raise ValueError("Для принта из каталога укажите print_size_id")

        return self


class CustomOrderOut(BaseModel):
    id: int
    product_type_id: int
    color_id: int
    size_label: str
    print_id: Optional[int]
    print_size_id: Optional[int]
    custom_images: Optional[list]
    comment: Optional[str]
    status: str
    admin_comment: Optional[str]
    recommended_price: Optional[Decimal]
    final_price: Optional[Decimal]
    carrier: str
    delivery_name: str
    delivery_phone: str
    delivery_city: str
    delivery_address: str
    created_at: datetime

    model_config = {"from_attributes": True}