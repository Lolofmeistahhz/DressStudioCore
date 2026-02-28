import os
from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    alert_chat_id: int
    admin_base_url: str

    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    SECRET_KEY: str
    DEBUG: bool = True

    BOT_TOKEN: str
    WEBHOOK_URL: str = ""

    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""

    UPLOAD_DIR: str = str(BASE_DIR / "media")

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    BASE_URL: str = os.getenv("BASE_URL")

    ADMIN_BASE_URL: str = f"{BASE_URL}/admin"


    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"


settings = Settings()