from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _create_token(subject: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int((now + expires_delta).timestamp())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def create_access_token(user_id: int) -> str:
    return _create_token(str(user_id), timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(user_id: int) -> str:
    return _create_token(str(user_id), timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))

def decode_access_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
