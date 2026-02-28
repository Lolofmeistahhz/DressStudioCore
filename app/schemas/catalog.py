from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ColorOut(BaseModel):
    id: int
    name: str
    hex_code: str
    palette_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductTypeSizeOut(BaseModel):
    id: int
    label: str
    length: Optional[str] = None
    width: Optional[str] = None
    sleeve: Optional[str] = None
    shoulders: Optional[str] = None
    waist_width: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductTypeColorOut(BaseModel):
    id: int
    color: ColorOut
    in_stock: bool
    palette_image_url: Optional[str] = None   # ← было обязательным, теперь Optional

    model_config = {"from_attributes": True}


class ProductTypeShort(BaseModel):
    id: int
    name: str
    slug: str
    base_price: Decimal
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductTypeDetail(BaseModel):
    id: int
    name: str
    slug: str
    base_price: Decimal
    description: Optional[str] = None
    image_url: Optional[str] = None
    size_chart_url: Optional[str] = None
    composition: Optional[str] = None
    notes: Optional[str] = None
    sizes: list[ProductTypeSizeOut]
    colors: list[ProductTypeColorOut]

    model_config = {"from_attributes": True}


class PrintSizeOut(BaseModel):
    id: int
    label: str
    price: Decimal

    model_config = {"from_attributes": True}


class PrintOut(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    sizes: list[PrintSizeOut]

    model_config = {"from_attributes": True}


class ReadyProductOut(BaseModel):
    id: int
    size_label: str
    price: Decimal
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    product_type: ProductTypeShort
    color: ColorOut

    model_config = {"from_attributes": True}