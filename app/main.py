import logging
import os
from contextlib import asynccontextmanager

from app.utils.shared import save_uploaded_file

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin

from app.api.users import router as users_router
from app.api.catalog import router as catalog_router
from app.api.cart import router as cart_router
from app.api.ready_orders import router as ready_orders_router
from app.api.custom_orders import router as custom_orders_router
from app.api.payments import router as payments_router

from app.core.config import settings
from app.core.database import sync_engine
from app.admin.auth import UsernameAndPasswordProvider
from app.admin.views import (
    UserAdmin, ColorAdmin, ProductTypeAdmin, ProductTypeSizeAdmin,
    ProductTypeColorAdmin, PrintAdmin, PrintSizeAdmin, ReadyProductAdmin,
    CartItemAdmin, ReadyOrderAdmin, CustomOrderAdmin,
    PaymentAdmin, CanvasTemplateAdmin, ConstructorOrderAdmin
)

from app.models.user import User
from app.models.catalog import (
    Color, ProductType, ProductTypeSize, ProductTypeColor,
    Print, PrintSize, ReadyProduct,
)
from app.models.order import CartItem, ReadyOrder, ReadyOrderItem, CustomOrder
from app.models.payment import Payment
from app.models.constructor import CanvasTemplate, ConstructorOrder


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sync_engine.dispose()


app = FastAPI(
    title="Embroidery Studio API",
    version="2.0.0",
    lifespan=lifespan,
)


# ── Админка ────────────────────────────────────────────────────────────────────

admin = Admin(
    sync_engine,
    title="Студия вышивки · Панель управления",
    auth_provider=UsernameAndPasswordProvider(),
    middlewares=[Middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)],
    templates_dir="templates/admin",
    base_url=settings.ADMIN_BASE_URL,  # важно для корректных ссылок по HTTPS
)


# ── Эндпоинт для загрузки файлов ──────────────────────────────────────────────

@app.post("/api/v1/upload", tags=["Upload"])
async def upload_file(file: UploadFile = File(...)):
    """
    Загружает файл на сервер и возвращает ссылку на него.
    Используется для загрузки изображений в админке.
    """

    if not file:
        raise HTTPException(status_code=400, detail="Файл не передан")

    file_url = await save_uploaded_file(file)

    if not file_url:
        raise HTTPException(status_code=500, detail="Не удалось сохранить файл")

    return {
        "success": True,
        "url": file_url
    }

admin.add_view(UserAdmin(User, label="Клиенты", icon="fa fa-users"))
admin.add_view(ColorAdmin(Color, label="Цвета", icon="fa fa-palette"))
admin.add_view(ProductTypeAdmin(ProductType, label="Типы изделий", icon="fa fa-shirt"))
admin.add_view(ProductTypeSizeAdmin(ProductTypeSize, label="Размеры", icon="fa fa-ruler"))
admin.add_view(ProductTypeColorAdmin(ProductTypeColor, label="Палитры", icon="fa fa-swatchbook"))
admin.add_view(PrintAdmin(Print, label="Принты / вышивки", icon="fa fa-image"))
admin.add_view(PrintSizeAdmin(PrintSize, label="Размеры вышивки", icon="fa fa-expand"))
admin.add_view(ReadyProductAdmin(ReadyProduct, label="Готовый мерч", icon="fa fa-box"))
admin.add_view(CartItemAdmin(CartItem, label="Корзины", icon="fa fa-cart-shopping"))
admin.add_view(ReadyOrderAdmin(ReadyOrder, label="Заказы мерча", icon="fa fa-bag-shopping"))
admin.add_view(CustomOrderAdmin(CustomOrder, label="Кастомные заказы", icon="fa fa-pen-nib"))
admin.add_view(PaymentAdmin(Payment, label="Платежи", icon="fa fa-credit-card"))
admin.add_view(CanvasTemplateAdmin(CanvasTemplate, label="Канвасы (конструктор)", icon="fa fa-vector-square"))
admin.add_view(ConstructorOrderAdmin(ConstructorOrder, label="Заказы конструктора", icon="fa fa-wand-magic-sparkles"))


# ── API роутеры ────────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

app.include_router(users_router, prefix=PREFIX)
app.include_router(catalog_router, prefix=PREFIX)
app.include_router(cart_router, prefix=PREFIX)
app.include_router(ready_orders_router, prefix=PREFIX)
app.include_router(custom_orders_router, prefix=PREFIX)
app.include_router(payments_router, prefix=PREFIX)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")

admin.mount_to(app)

@app.get("/")
async def root():
    return {"message": "Embroidery Studio API v1 🧵"}


