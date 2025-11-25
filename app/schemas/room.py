from pydantic import BaseModel
from typing import Optional
from enum import Enum

# --- Enumeración del tipo de habitación ---
class RoomType(str, Enum):
    HABITACION = "HABITACION"
    DEPARTAMENTO = "DEPARTAMENTO"


# --- Base con campos comunes ---
class RoomBase(BaseModel):
    residence_id: int
    title: str
    description: Optional[str] = None
    type: RoomType = RoomType.HABITACION
    capacity: int = 1
    price_per_month: float
    has_private_bath: bool = False
    is_available: bool = True
    image_url: Optional[str] = None  # ✅ agregado aquí también (opcional)


# --- Creación (usa los mismos campos que Base) ---
class RoomCreate(RoomBase):
    pass


# --- Actualización (solo los editables, todos opcionales) ---
class RoomUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[RoomType] = None
    capacity: Optional[int] = None
    price_per_month: Optional[float] = None
    has_private_bath: Optional[bool] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None

    class Config:
        orm_mode = True


# --- Salida (respuesta) ---
class RoomOut(RoomBase):
    id: int

    class Config:
        orm_mode = True
