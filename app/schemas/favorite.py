from pydantic import BaseModel
from typing import Optional

class FavoriteToggle(BaseModel):
    room_id: Optional[int] = None
    residence_id: Optional[int] = None

class FavoriteOut(BaseModel):
    id: int
    user_id: int
    room_id: int | None = None
    residence_id: int | None = None
