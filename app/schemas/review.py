from pydantic import BaseModel, conint
from typing import Optional

class ReviewCreate(BaseModel):
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None
    room_id: Optional[int] = None
    residence_id: Optional[int] = None

class ReviewOut(BaseModel):
    id: int
    user_id: int | None
    rating: int
    comment: str | None
    room_id: int | None
    residence_id: int | None
