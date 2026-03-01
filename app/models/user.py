from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    client = "client"
    admin  = "admin"


class DeliveryCarrier(str, enum.Enum):
    cdek   = "cdek"
    yandex = "yandex"


class User(Base):
    __tablename__ = "users"

    id:               Mapped[int]           = mapped_column(primary_key=True)
    telegram_id:      Mapped[int]           = mapped_column(BigInteger, unique=True, index=True)
    username:         Mapped[str | None]    = mapped_column(String(100))
    full_name:        Mapped[str | None]    = mapped_column(String(200))
    phone:            Mapped[str | None]    = mapped_column(String(20))  # единственный телефон
    role:             Mapped[UserRole]      = mapped_column(
                                                SAEnum(UserRole, name="userrole"),
                                                default=UserRole.client,
                                                server_default="client",
                                            )

    # Данные доставки (phone переиспользуется как delivery_phone)
    delivery_name:    Mapped[str | None]    = mapped_column(String(200))
    delivery_city:    Mapped[str | None]    = mapped_column(String(100))
    delivery_address: Mapped[str | None]    = mapped_column(String(500))
    delivery_carrier: Mapped[DeliveryCarrier | None] = mapped_column(
                                                SAEnum(DeliveryCarrier, name="deliverycarrier"),
                                                nullable=True,
                                            )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cart_items:    Mapped[list["CartItem"]]    = relationship(back_populates="user", cascade="all, delete-orphan")
    ready_orders:  Mapped[list["ReadyOrder"]]  = relationship(back_populates="user")
    custom_orders: Mapped[list["CustomOrder"]] = relationship(back_populates="user")

    @property
    def delivery_complete(self) -> bool:
        """Все поля доставки заполнены."""
        return all([
            self.delivery_name,
            self.phone,            # телефон один — из профиля
            self.delivery_city,
            self.delivery_address,
            self.delivery_carrier,
        ])