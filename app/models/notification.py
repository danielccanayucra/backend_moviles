from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from app.db.session import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    body = Column(String(1000))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
