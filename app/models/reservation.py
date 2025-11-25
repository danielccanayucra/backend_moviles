from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
from enum import Enum as PyEnum


class ReservationStatus(str, PyEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    total_price = Column(Float, default=0.0)

    # ✅ Relaciones
    room = relationship("Room", back_populates="reservations")
    student = relationship("User", foreign_keys=[student_id])

    # ✅ Relación con contrato (1:1)
    contract = relationship("Contract", back_populates="reservation", uselist=False)
    contract_details = relationship("ContractDetails", back_populates="reservation", uselist=False)

    def __repr__(self):
        return f"<Reservation id={self.id} room_id={self.room_id} student_id={self.student_id}>"
