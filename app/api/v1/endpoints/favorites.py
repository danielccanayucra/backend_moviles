from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteToggle, FavoriteOut

router = APIRouter()

@router.post("/toggle", response_model=FavoriteOut)
def toggle_favorite(data: FavoriteToggle, db: Session = Depends(get_db), current=Depends(get_current_user)):
    if not data.room_id and not data.residence_id:
        raise HTTPException(status_code=400, detail="room_id o residence_id requerido")
    q = db.query(Favorite).filter(Favorite.user_id == current.id)
    if data.room_id:
        q = q.filter(Favorite.room_id == data.room_id)
    else:
        q = q.filter(Favorite.room_id.is_(None))
    if data.residence_id:
        q = q.filter(Favorite.residence_id == data.residence_id)
    else:
        q = q.filter(Favorite.residence_id.is_(None))
    fav = q.first()
    if fav:
        db.delete(fav)
        db.commit()
        return FavoriteOut(id=-1, user_id=current.id, room_id=data.room_id, residence_id=data.residence_id)
    fav = Favorite(user_id=current.id, room_id=data.room_id, residence_id=data.residence_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return FavoriteOut(id=fav.id, user_id=fav.user_id, room_id=fav.room_id, residence_id=fav.residence_id)

@router.get("/", response_model=List[FavoriteOut])
def list_favorites(db: Session = Depends(get_db), current=Depends(get_current_user)):
    items = db.query(Favorite).filter(Favorite.user_id == current.id).all()
    return [FavoriteOut(id=i.id, user_id=i.user_id, room_id=i.room_id, residence_id=i.residence_id) for i in items]
