from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ColorOut(BaseModel):
    id: int
    name: str
    hex_code: str
    model_config = {"from_attributes": True}


class ProductTypeSizeOut(BaseModel):
    id: int
    label: str
    length:      Optional[str] = None
    width:       Optional[str] = None
    sleeve:      Optional[str] = None
    shoulders:   Optional[str] = None
    waist_width: Optional[str] = None
    model_config = {"from_attributes": True}


class ProductTypeColorOut(BaseModel):
    id: int
    color: ColorOut
    in_stock: bool
    model_config = {"from_attributes": True}


class ProductTypeShort(BaseModel):
    id: int
    name: str
    slug: str
    base_price:        Decimal
    size_chart_url:    Optional[str] = None
    color_palette_url: Optional[str] = None
    model_config = {"from_attributes": True}


class ProductTypeDetail(BaseModel):
    id: int
    name: str
    slug: str
    base_price:        Decimal
    description:       Optional[str] = None
    size_chart_url:    Optional[str] = None
    color_palette_url: Optional[str] = None
    composition:       Optional[str] = None
    notes:             Optional[str] = None
    sizes:  list[ProductTypeSizeOut]  = []
    colors: list[ProductTypeColorOut] = []
    model_config = {"from_attributes": True}


# ── Названия продуктов внутри типа ───────────────────────────────────────────

class ProductNameInfo(BaseModel):
    """
    Уникальное название товара внутри типа.
    available_color_ids — цвета у которых есть stock > 0 хотя бы в одном размере.
    """
    name: str
    available_color_ids: list[int]
    total_count: int


class PrintSizeOut(BaseModel):
    id: int
    label: str
    price: Decimal
    model_config = {"from_attributes": True}


class PrintOut(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    sizes: list[PrintSizeOut] = []
    model_config = {"from_attributes": True}


class ReadyProductOut(BaseModel):
    id: int
    name: str
    size_label: str
    price: Decimal
    stock_quantity: int
    image_url: Optional[str] = None
    is_active: bool
    product_type: ProductTypeShort
    color: ColorOut
    model_config = {"from_attributes": True}