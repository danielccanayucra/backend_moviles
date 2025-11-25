from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, require_role
from app.models.user import UserRole, User
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter()

@router.post("/", response_model=ReviewOut)
def create_review(data: ReviewCreate, db: Session = Depends(get_db), current: User = Depends(require_role(UserRole.STUDENT, UserRole.SUPERADMIN))):
    if not data.room_id and not data.residence_id:
        raise HTTPException(status_code=400, detail="Debe indicar room_id o residence_id")
    review = Review(
        user_id=current.id if current.role == UserRole.STUDENT else None,
        room_id=data.room_id, residence_id=data.residence_id,
        rating=data.rating, comment=data.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return ReviewOut(id=review.id, user_id=review.user_id, rating=review.rating, comment=review.comment, room_id=review.room_id, residence_id=review.residence_id)

@router.get("/", response_model=List[ReviewOut])
def list_reviews(db: Session = Depends(get_db), room_id: int | None = None, residence_id: int | None = None):
    q = db.query(Review)
    if room_id:
        q = q.filter(Review.room_id == room_id)
    if residence_id:
        q = q.filter(Review.residence_id == residence_id)
    items = q.order_by(Review.id.desc()).all()
    return [ReviewOut(id=i.id, user_id=i.user_id, rating=i.rating, comment=i.comment, room_id=i.room_id, residence_id=i.residence_id) for i in items]
