from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, require_role, get_current_user
from app.models.user import UserRole, User
from app.models.residence import Residence
from app.schemas.residence import ResidenceCreate, ResidenceOut, ResidenceUpdate

router = APIRouter()

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