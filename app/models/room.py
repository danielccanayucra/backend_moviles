from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class RoomType(str, enum.Enum):
    HABITACION = "HABITACION"
    DEPARTAMENTO = "DEPARTAMENTO"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    residence_id = Column(Integer, ForeignKey("residences.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(RoomType), nullable=False, default=RoomType.HABITACION)
    capacity = Column(Integer, nullable=False, default=1)
    price_per_month = Column(Float, nullable=False)
    has_private_bath = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)


    # ✅ Relaciones
    residence = relationship("Residence", back_populates="rooms")
    reservations = relationship("Reservation", back_populates="room", cascade="all, delete-orphan")
