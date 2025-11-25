from typing import List, Optional
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role
from app.schemas.user import UserOut, UserUpdate
from app.models.user import User, UserRole
from app.core.config import settings

router = APIRouter()

# Carpeta donde se guardan las imágenes
USERS_MEDIA_ROOT = os.path.join("media", "users")


@router.get("/me", response_model=UserOut)
def me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).get(current.id)
    return user


@router.get("/", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current=Depends(require_role(UserRole.SUPERADMIN))
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current=Depends(require_role(UserRole.SUPERADMIN)),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current=Depends(require_role(UserRole.SUPERADMIN)),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()

    return {"detail": "Usuario eliminado correctamente"}


@router.put("/me", response_model=UserOut)
def update_me(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    user = db.query(User).get(current.id)

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# -------------------------------------------------------
# 🚀 SUBIR IMAGEN DE PERFIL
# -------------------------------------------------------
@router.post("/me/profile-picture", response_model=UserOut)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")

    # Crear carpeta si no existe
    os.makedirs(USERS_MEDIA_ROOT, exist_ok=True)

    # Nombre único
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext:
        ext = ".jpg"

    file_name = f"user_{current_user.id}_{uuid.uuid4().hex}{ext}"

    # Guardar archivo
    file_path = os.path.join(USERS_MEDIA_ROOT, file_name)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # URL pública completa
    base_url = settings.BASE_URL.rstrip("/")
    public_url = f"{base_url}/media/users/{file_name}"

    # Guardar en BD
    current_user.profile_picture = public_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user
