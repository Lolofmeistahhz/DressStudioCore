from typing import Optional
from pydantic import BaseModel
from app.models.user import DeliveryCarrier


class UserUpsert(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None


class DeliveryUpdate(BaseModel):
    delivery_name:    Optional[str]             = None
    delivery_city:    Optional[str]             = None
    delivery_address: Optional[str]             = None
    delivery_carrier: Optional[DeliveryCarrier] = None


class PhoneUpdate(BaseModel):
    phone: str


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username:         Optional[str] = None
    full_name:        Optional[str] = None
    phone:            Optional[str] = None
    role: str
    delivery_name:    Optional[str] = None
    delivery_city:    Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_carrier: Optional[str] = None
    delivery_complete: bool

    model_config = {"from_attributes": True}