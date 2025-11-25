from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.user import UserOut, UserUpdate
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/me", response_model=UserOut)
def me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).get(current.id)  # type: ignore
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)  # type: ignore
@router.get("/", response_model=List[UserOut])
def list_users(role: Optional[UserRole] = None, db: Session = Depends(get_db), current=Depends(require_role(UserRole.SUPERADMIN))):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db), current=Depends(require_role(UserRole.SUPERADMIN))):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current=Depends(require_role(UserRole.SUPERADMIN))):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}
@router.put("/me", response_model=UserOut)
def update_me(update_data: UserUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    user = db.query(User).get(current.id)
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
