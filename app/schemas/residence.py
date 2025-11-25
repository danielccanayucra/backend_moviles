from pydantic import BaseModel
from typing import Optional


# --- Base con los campos comunes ---
class ResidenceBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None  # ✅ Campo opcional para imagen


# --- Creación ---
class ResidenceCreate(ResidenceBase):
    pass


# --- Actualización (PUT) ---
class ResidenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True  # ✅ reemplaza orm_mode (nuevo en Pydantic v2)


# --- Salida (respuesta) ---
class ResidenceOut(ResidenceBase):
    id: int
    owner_id: Optional[int] = None  # ✅ evita errores con valores nulos

    class Config:
        from_attributes = True  # ✅ necesario para convertir desde SQLAlchemy
