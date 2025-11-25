from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, func
import enum
from app.db.session import Base
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship



class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    OWNER = "OWNER"
    SUPERADMIN = "SUPERADMIN"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    profile_picture = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

residences = relationship("Residence", back_populates="owner")
