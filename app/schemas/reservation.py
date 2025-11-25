from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from enum import Enum
from typing import Optional


# --------------------------------------
# ENUM de estados de reserva
# --------------------------------------
class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


# --------------------------------------
# SCHEMA: Creación de reservas
# --------------------------------------
class ReservationCreate(BaseModel):
    room_id: int
    start_date: datetime
    end_date: datetime

    @field_validator("end_date")
    @classmethod
    def check_dates(cls, v: datetime, info: ValidationInfo) -> datetime:
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("La fecha de fin debe ser mayor que la fecha de inicio")
        return v


# --------------------------------------
# SCHEMA: Salida de reserva (con datos extendidos)
# --------------------------------------
class ReservationOut(BaseModel):
    id: int
    room_id: int
    student_id: Optional[int]
    start_date: datetime
    end_date: datetime
    status: ReservationStatus
    total_price: Optional[float] = None

    # 👇 Campos adicionales para contrato
    owner_name: Optional[str] = None
    student_name: Optional[str] = None
    residence_name: Optional[str] = None
    residence_address: Optional[str] = None
    room_price: Optional[float] = None

    class Config:
        from_attributes = True  # equivale a orm_mode = True (FastAPI 0.115+)
