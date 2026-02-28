from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.catalog import (
    ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.schemas.catalog import (
    ProductTypeShort, ProductTypeDetail, ProductTypeColorOut,
    ProductTypeSizeOut, PrintOut, ReadyProductOut,
)

router = APIRouter(prefix="/catalog", tags=["Каталог"])


@router.get("/types", response_model=list[ProductTypeShort], summary="Все типы изделий")
async def get_product_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductType).where(ProductType.is_active == True)
    )
    return result.scalars().all()


@router.get("/types/{type_id}", response_model=ProductTypeDetail, summary="Тип изделия с размерами и цветами")
async def get_product_type(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductType)
        .options(
            selectinload(ProductType.sizes),
            selectinload(ProductType.colors).selectinload(ProductTypeColor.color),
        )
        .where(ProductType.id == type_id, ProductType.is_active == True)
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Тип изделия не найден")
    return pt


@router.get("/types/{type_id}/colors", response_model=list[ProductTypeColorOut], summary="Доступные цвета")
async def get_type_colors(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductTypeColor)
        .options(selectinload(ProductTypeColor.color))
        .where(ProductTypeColor.product_type_id == type_id)
    )
    return result.scalars().all()


@router.get("/types/{type_id}/sizes", response_model=list[ProductTypeSizeOut], summary="Размерная сетка")
async def get_type_sizes(type_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductTypeSize).where(ProductTypeSize.product_type_id == type_id)
    )
    return result.scalars().all()


@router.get("/prints", response_model=list[PrintOut], summary="Каталог принтов/вышивок")
async def get_prints(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Print)
        .options(selectinload(Print.sizes))
        .where(Print.is_active == True)
    )
    return result.scalars().all()


@router.get("/prints/{print_id}", response_model=PrintOut, summary="Принт с размерами")
async def get_print(print_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Print)
        .options(selectinload(Print.sizes))
        .where(Print.id == print_id, Print.is_active == True)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Принт не найден")
    return p


@router.get("/ready", response_model=list[ReadyProductOut], summary="Готовый мерч на складе")
async def get_ready_products(
    product_type_id: Optional[int] = None,
    color_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ReadyProduct)
        .options(
            selectinload(ReadyProduct.product_type),
            selectinload(ReadyProduct.color),
        )
        .where(ReadyProduct.is_active == True, ReadyProduct.stock_quantity > 0)
    )
    if product_type_id:
        query = query.where(ReadyProduct.product_type_id == product_type_id)
    if color_id:
        query = query.where(ReadyProduct.color_id == color_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/ready/{product_id}", response_model=ReadyProductOut, summary="Конкретный товар")
async def get_ready_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReadyProduct)
        .options(
            selectinload(ReadyProduct.product_type),
            selectinload(ReadyProduct.color),
        )
        .where(ReadyProduct.id == product_id, ReadyProduct.is_active == True)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return p