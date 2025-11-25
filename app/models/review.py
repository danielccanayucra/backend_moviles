from sqlalchemy import Column, Integer, Text, SmallInteger, ForeignKey, DateTime, func
from app.db.session import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)
    residence_id = Column(Integer, ForeignKey("residences.id", ondelete="CASCADE"), nullable=True)
    rating = Column(SmallInteger, nullable=False)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
