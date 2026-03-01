"""
app/api/catalog.py
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.catalog import (
    ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.schemas.catalog import (
    ProductTypeShort, ProductTypeDetail,
    ProductTypeSizeOut, ProductTypeColorOut,
    PrintOut, ReadyProductOut, ProductNameInfo,
)
from app.utils.shared import media_url   # ← media_url вместо full_url

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _patch_type(t: ProductType):
    t.size_chart_url    = media_url(t.size_chart_url)
    t.color_palette_url = media_url(t.color_palette_url)


@router.get("/types", response_model=list[ProductTypeShort])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductType).where(ProductType.is_active == True).order_by(ProductType.id)
    )
    types = result.scalars().all()
    for t in types:
        _patch_type(t)
    return types


@router.get("/types/{type_id}", response_model=ProductTypeDetail)
async def get_type(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductType)
        .where(ProductType.id == type_id)
        .options(
            selectinload(ProductType.sizes),
            selectinload(ProductType.colors).selectinload(ProductTypeColor.color),
        )
    )
    pt = result.scalar_one_or_none()
    if pt:
        _patch_type(pt)
    return pt


@router.get("/types/{type_id}/sizes", response_model=list[ProductTypeSizeOut])
async def get_type_sizes(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductTypeSize)
        .where(ProductTypeSize.product_type_id == type_id)
        .order_by(ProductTypeSize.id)
    )
    return result.scalars().all()


@router.get("/types/{type_id}/colors", response_model=list[ProductTypeColorOut])
async def get_type_colors(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductTypeColor)
        .where(ProductTypeColor.product_type_id == type_id)
        .options(selectinload(ProductTypeColor.color))
        .order_by(ProductTypeColor.id)
    )
    return result.scalars().all()


@router.get("/types/{type_id}/names", response_model=list[ProductNameInfo])
async def get_type_product_names(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReadyProduct)
        .where(ReadyProduct.product_type_id == type_id, ReadyProduct.is_active == True)
    )
    products = result.scalars().all()

    name_map: dict[str, dict] = {}
    for p in products:
        if p.name not in name_map:
            name_map[p.name] = {"available_color_ids": set(), "total_count": 0}
        name_map[p.name]["total_count"] += 1
        if p.stock_quantity > 0:
            name_map[p.name]["available_color_ids"].add(p.color_id)

    return [
        ProductNameInfo(
            name=name,
            available_color_ids=sorted(data["available_color_ids"]),
            total_count=data["total_count"],
        )
        for name, data in name_map.items()
    ]


@router.get("/ready", response_model=list[ReadyProductOut])
async def list_ready(
    product_type_id: int | None = Query(None),
    color_id:        int | None = Query(None),
    name:            str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(ReadyProduct).where(ReadyProduct.is_active == True)
    if product_type_id:
        q = q.where(ReadyProduct.product_type_id == product_type_id)
    if color_id:
        q = q.where(ReadyProduct.color_id == color_id)
    if name:
        q = q.where(ReadyProduct.name == name)
    q = q.options(
        selectinload(ReadyProduct.product_type),
        selectinload(ReadyProduct.color),
    )
    result   = await db.execute(q)
    products = result.scalars().all()
    for p in products:
        p.image_url = media_url(p.image_url)
    return products


@router.get("/prints", response_model=list[PrintOut])
async def list_prints(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Print)
        .where(Print.is_active == True)
        .options(selectinload(Print.sizes))
        .order_by(Print.id)
    )
    prints = result.scalars().all()
    for p in prints:
        p.image_url = media_url(p.image_url)
    return prints