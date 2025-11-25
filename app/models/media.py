from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.session import Base

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    owner_type = Column(String(50))  # 'residence' | 'room'
    owner_id = Column(Integer)       # id de la entidad
    path = Column(String(500), nullable=False)  # ruta local o URL
    created_at = Column(DateTime, server_default=func.now())
