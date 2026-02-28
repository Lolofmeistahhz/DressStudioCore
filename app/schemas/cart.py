from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.schemas.catalog import ColorOut, ProductTypeShort


class CartItemAdd(BaseModel):
    ready_product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class ReadyProductShort(BaseModel):
    id: int
    size_label: str
    price: Decimal
    image_url: Optional[str]
    product_type: ProductTypeShort
    color: ColorOut

    model_config = {"from_attributes": True}


class CartItemOut(BaseModel):
    id: int
    ready_product: ReadyProductShort
    quantity: int
    subtotal: Decimal

    model_config = {"from_attributes": True}


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
    items_count: int