from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class PaymentEntityType(str, enum.Enum):
    ready_order       = "ready_order"
    custom_order      = "custom_order"
    constructor_order = "constructor_order"


class PaymentStatus(str, enum.Enum):
    pending   = "pending"
    succeeded = "succeeded"
    cancelled = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id:                  Mapped[int]               = mapped_column(primary_key=True)
    entity_type:         Mapped[PaymentEntityType] = mapped_column(
                             SAEnum(PaymentEntityType, name="paymententitytype"),
                         )
    entity_id:           Mapped[int]               = mapped_column()
    amount:              Mapped[Decimal]            = mapped_column(Numeric(10, 2))
    status:              Mapped[PaymentStatus]      = mapped_column(
                             SAEnum(PaymentStatus, name="paymentstatus"),
                             default=PaymentStatus.pending,
                         )
    yookassa_payment_id: Mapped[str | None]         = mapped_column(String(100), nullable=True)
    created_at:          Mapped[datetime]           = mapped_column(DateTime, server_default=func.now())