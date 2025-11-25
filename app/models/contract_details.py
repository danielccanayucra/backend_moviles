from sqlalchemy import Column, Integer, String, Text, Float, Date, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.db.session import Base


class ContractDetailsStatus(str, PyEnum):
    DRAFT = "DRAFT"      # Editando
    READY = "READY"      # Listo para generar contrato/pdf
    CANCELLED = "CANCELLED"


class ContractDetails(Base):
    __tablename__ = "contract_details"

    id = Column(Integer, primary_key=True, index=True)

    # Relaciones principales
    reservation_id = Column(Integer, ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Información editable del contrato
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    monthly_price = Column(Float, nullable=False)
    deposit_amount = Column(Float, nullable=True)
    payment_day = Column(Integer, nullable=True)  # día de pago (1–31)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    included_services = Column(Text, nullable=True)  # ej: agua, luz, wifi
    rules = Column(Text, nullable=True)             # reglas de la residencia
    extra_conditions = Column(Text, nullable=True)  # campo libre para texto adicional

    status = Column(Enum(ContractDetailsStatus), nullable=False, default=ContractDetailsStatus.DRAFT)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relaciones ORM
    reservation = relationship("Reservation", back_populates="contract_details")
    room = relationship("Room")
    student = relationship("User", foreign_keys=[student_id])
    owner = relationship("User", foreign_keys=[owner_id])