# app/schemas/contract.py
from datetime import datetime
from pydantic import BaseModel


class ContractOut(BaseModel):
    id: int
    reservation_id: int
    details_id: int           # 🔹 nuevo campo en el schema
    pdf_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True  # antes orm_mode = True