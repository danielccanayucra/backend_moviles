from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(settings.DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

def init_db():
    print("🚀 Iniciando aplicación...BS")
    from app.models import user, profile, residence, room, reservation, review, favorite, media, chat, notification
    Base.metadata.create_all(bind=engine)
