from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime, func
from app.db.session import Base

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)
    residence_id = Column(Integer, ForeignKey("residences.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'room_id', name='uq_user_room'),
        UniqueConstraint('user_id', 'residence_id', name='uq_user_residence'),
    )
