from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Residence(Base):
    __tablename__ = "residences"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(String(255), nullable=True)
    address = Column(String(255))
    district = Column(String(100))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    # 🔗 Relación con habitaciones
    rooms = relationship("Room", back_populates="residence", cascade="all, delete-orphan")
owner = relationship("User", back_populates="residences")
