from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class ContractDetailsStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    CANCELLED = "CANCELLED"


class ContractDetailsBase(BaseModel):
    title: str
    description: Optional[str] = None
    monthly_price: float
    deposit_amount: Optional[float] = None
    payment_day: Optional[int] = None
    start_date: date
    end_date: date
    included_services: Optional[str] = None
    rules: Optional[str] = None
    extra_conditions: Optional[str] = None


class ContractDetailsCreate(ContractDetailsBase):
    reservation_id: int
    room_id: Optional[int] = None
    student_id: Optional[int] = None
    owner_id: Optional[int] = None


class ContractDetailsUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    monthly_price: Optional[float] = None
    deposit_amount: Optional[float] = None
    payment_day: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    included_services: Optional[str] = None
    rules: Optional[str] = None
    extra_conditions: Optional[str] = None
    status: Optional[ContractDetailsStatus] = None


class ContractDetailsOut(ContractDetailsBase):
    id: int
    reservation_id: int
    room_id: Optional[int]
    student_id: Optional[int]
    owner_id: Optional[int]
    status: ContractDetailsStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True