from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id", ondelete="CASCADE"))
    details_id = Column(Integer, ForeignKey("contract_details.id", ondelete="CASCADE"), nullable=False)
    pdf_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relaciones
    reservation = relationship("Reservation", back_populates="contract")
    contract_details = relationship("ContractDetails")