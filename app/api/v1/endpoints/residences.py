import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, require_role, get_current_user
from app.models.user import UserRole, User
from app.models.residence import Residence
from app.schemas.residence import ResidenceCreate, ResidenceOut, ResidenceUpdate
from app.core.config import settings

router = APIRouter()
MEDIA_ROOT = "media"
RESIDENCES_MEDIA_ROOT = os.path.join(MEDIA_ROOT, "residences")

@router.post("/", response_model=ResidenceOut)
def create_residence(data: ResidenceCreate, db: Session = Depends(get_db), current=Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN))):
    res = Residence(owner_id=current.id, **data.dict())
    db.add(res)
    db.commit()
    db.refresh(res)
    return ResidenceOut(id=res.id, owner_id=res.owner_id, **data.dict())

@router.get("/", response_model=List[ResidenceOut])
def list_residences(db: Session = Depends(get_db)):
    items = db.query(Residence).all()
    return [ResidenceOut(id=i.id, owner_id=i.owner_id, name=i.name, description=i.description, address=i.address, district=i.district, city=i.city, latitude=i.latitude, longitude=i.longitude) for i in items]
@router.post("/{residence_id}/image-url", response_model=ResidenceOut)
async def upload_residence_main_image(
    residence_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    # 1) Validar que sea una imagen
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")

    # 2) Buscar residencia
    residence = db.query(Residence).get(residence_id)
    if not residence:
        raise HTTPException(status_code=404, detail="Residencia no encontrada")

    # (Opcional) verificar que el owner sea dueño de esa residencia
    # if current_user.role == UserRole.OWNER and residence.owner_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="No puedes modificar esta residencia")

    # 3) Asegurar carpeta
    os.makedirs(RESIDENCES_MEDIA_ROOT, exist_ok=True)

    # 4) Generar nombre único
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext:
        ext = ".jpg"

    filename = f"res_{residence_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(RESIDENCES_MEDIA_ROOT, filename)

    # 5) Guardar archivo
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 6) Construir URL pública
    base_url = settings.BASE_URL.rstrip("/")
    public_url = f"{base_url}/media/residences/{filename}"

    # 7) Guardar en BD
    residence.main_image = public_url
    db.add(residence)
    db.commit()
    db.refresh(residence)

    return residence
@router.get("/{residence_id}", response_model=ResidenceOut)
def get_residence(residence_id: int, db: Session = Depends(get_db)):
    res = db.query(Residence).get(residence_id)
    if not res:
        raise HTTPException(status_code=404, detail="No encontrado")
    return ResidenceOut(id=res.id, owner_id=res.owner_id, name=res.name, description=res.description, address=res.address, district=res.district, city=res.city, latitude=res.latitude, longitude=res.longitude)
@router.put("/{residence_id}", response_model=ResidenceOut)
def update_residence(residence_id: int, update_data: ResidenceUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    residence = db.query(Residence).get(residence_id)
    if not residence:
        raise HTTPException(status_code=404, detail="Residencia no encontrada")

    if current.role != UserRole.SUPERADMIN and residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado para editar esta residencia")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(residence, field, value)

    db.commit()
    db.refresh(residence)
    return residence


@router.delete("/{residence_id}")
def delete_residence(residence_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    residence = db.query(Residence).get(residence_id)
    if not residence:
        raise HTTPException(status_code=404, detail="Residencia no encontrada")

    if current.role != UserRole.SUPERADMIN and residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar esta residencia")

    db.delete(residence)
    db.commit()
    return {"detail": "Residencia eliminada correctamente"}
# 🔹 Nuevo endpoint: listar residencias por propietario (owner)
@router.get("/owner/{owner_id}", response_model=List[ResidenceOut])
def list_residences_by_owner(
    owner_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    """
    🔹 Devuelve todas las residencias pertenecientes a un propietario (owner)
    """

    residencias = db.query(Residence).filter(Residence.owner_id == owner_id).all()

    if not residencias:
        raise HTTPException(status_code=404, detail="No se encontraron residencias para este propietario")

    return [
        ResidenceOut(
            id=r.id,
            name=r.name,
            description=r.description,
            address=r.address,
            district=r.district,
            city=r.city,
            image_url=r.image_url,
            latitude=r.latitude,
            longitude=r.longitude,
            owner_id=r.owner_id,
        )
        for r in residencias
    ]
