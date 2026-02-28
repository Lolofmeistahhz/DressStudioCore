from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.models.payment import PaymentEntityType, PaymentStatus


class PaymentCreate(BaseModel):
    entity_type: PaymentEntityType
    entity_id: int
    amount: Decimal


class PaymentInitResponse(BaseModel):
    payment_id: int
    yookassa_payment_id: str
    confirmation_url: str
    amount: Decimal


class PaymentOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    amount: Decimal
    status: str
    yookassa_payment_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}