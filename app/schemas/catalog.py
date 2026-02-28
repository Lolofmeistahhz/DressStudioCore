from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ColorOut(BaseModel):
    id: int
    name: str
    hex_code: str
    palette_image_url: Optional[str]

    model_config = {"from_attributes": True}


class ProductTypeSizeOut(BaseModel):
    id: int
    label: str
    length: Optional[str]
    width: Optional[str]
    sleeve: Optional[str]
    shoulders: Optional[str]
    waist_width: Optional[str]

    model_config = {"from_attributes": True}


class ProductTypeColorOut(BaseModel):
    id: int
    color: ColorOut
    in_stock: bool
    palette_image_url: Optional[str]

    model_config = {"from_attributes": True}


class ProductTypeShort(BaseModel):
    id: int
    name: str
    slug: str
    base_price: Decimal
    image_url: Optional[str]

    model_config = {"from_attributes": True}


class ProductTypeDetail(BaseModel):
    id: int
    name: str
    slug: str
    base_price: Decimal
    description: Optional[str]
    image_url: Optional[str]
    size_chart_url: Optional[str]
    composition: Optional[str]
    notes: Optional[str]
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
    image_url: Optional[str]
    sizes: list[PrintSizeOut]

    model_config = {"from_attributes": True}


class ReadyProductOut(BaseModel):
    id: int
    size_label: str
    price: Decimal
    stock_quantity: int
    image_url: Optional[str]
    is_active: bool
    product_type: ProductTypeShort
    color: ColorOut

    model_config = {"from_attributes": True}