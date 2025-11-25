from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.api.deps import get_db, require_role, get_current_user
from app.models.user import UserRole
from app.models.room import Room, RoomType
from app.models.residence import Residence
from app.schemas.room import RoomCreate, RoomOut, RoomUpdate

router = APIRouter()

# ✅ Crear habitación
@router.post("/", response_model=RoomOut)
def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    current=Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN))
):
    room = Room(**data.dict())
    db.add(room)
    db.commit()
    db.refresh(room)
    return RoomOut.model_validate(room, from_attributes=True)

# ✅ Listar habitaciones (con filtros + control por rol)
@router.get("/", response_model=List[RoomOut])
def list_rooms(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    residence_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    capacity: Optional[int] = None,
    room_type: Optional[RoomType] = Query(default=None, alias="type"),  # alias "type"
):
    q = db.query(Room)

    # Filtro por residencia
    if residence_id is not None:
        q = q.filter(Room.residence_id == residence_id)

    # Filtro por ciudad o distrito
    if city:
        q = q.join(Room.residence).filter(
            or_(
                Residence.city.ilike(f"%{city}%"),
                Residence.district.ilike(f"%{city}%"),
            )
        )

    # Filtros adicionales
    if min_price is not None:
        q = q.filter(Room.price_per_month >= min_price)
    if max_price is not None:
        q = q.filter(Room.price_per_month <= max_price)
    if room_type is not None:
        q = q.filter(Room.type == room_type)
    if capacity is not None:
        q = q.filter(Room.capacity >= capacity)

    # 🔒 Regla de visibilidad por rol:
    # - STUDENT: solo ve habitaciones disponibles
    # - OWNER / SUPERADMIN: ven todas
    if current_user.role == UserRole.STUDENT:
        q = q.filter(Room.is_available.is_(True))

    rooms = q.all()

    result = []
    for r in rooms:
        result.append(
            RoomOut(
                id=r.id,
                residence_id=r.residence_id,
                title=r.title,
                description=r.description,
                image_url=getattr(r, "image_url", None),
                type=getattr(r, "type", RoomType.HABITACION),
                capacity=getattr(r, "capacity", 1),
                price_per_month=r.price_per_month,
                has_private_bath=getattr(r, "has_private_bath", False),
                is_available=getattr(r, "is_available", True),
            )
        )

    return result

# 🌐 Endpoint público: solo habitaciones disponibles, sin autenticación
@router.get("/public", response_model=List[RoomOut])
def list_public_rooms(
    db: Session = Depends(get_db),
    residence_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    capacity: Optional[int] = None,
    room_type: Optional[RoomType] = Query(default=None, alias="type"),
):
    q = db.query(Room)

    # Filtro por residencia
    if residence_id is not None:
        q = q.filter(Room.residence_id == residence_id)

    # Filtro por ciudad o distrito
    if city:
        q = q.join(Room.residence).filter(
            or_(
                Residence.city.ilike(f"%{city}%"),
                Residence.district.ilike(f"%{city}%"),
            )
        )

    # Filtros adicionales
    if min_price is not None:
        q = q.filter(Room.price_per_month >= min_price)
    if max_price is not None:
        q = q.filter(Room.price_per_month <= max_price)
    if room_type is not None:
        q = q.filter(Room.type == room_type)
    if capacity is not None:
        q = q.filter(Room.capacity >= capacity)

    # Público => siempre solo habitaciones disponibles
    q = q.filter(Room.is_available.is_(True))

    rooms = q.all()

    result = []
    for r in rooms:
        result.append(
            RoomOut(
                id=r.id,
                residence_id=r.residence_id,
                title=r.title,
                description=r.description,
                image_url=getattr(r, "image_url", None),
                type=getattr(r, "type", RoomType.HABITACION),
                capacity=getattr(r, "capacity", 1),
                price_per_month=r.price_per_month,
                has_private_bath=getattr(r, "has_private_bath", False),
                is_available=getattr(r, "is_available", True),
            )
        )

    return result

# ✅ Obtener habitación por ID
@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="No encontrado")

    return RoomOut(
        id=room.id,
        residence_id=room.residence_id,
        title=room.title,
        description=room.description,
        image_url=getattr(room, "image_url", None),
        type=getattr(room, "type", RoomType.HABITACION),
        capacity=getattr(room, "capacity", 1),
        price_per_month=room.price_per_month,
        has_private_bath=getattr(room, "has_private_bath", False),
        is_available=getattr(room, "is_available", True),
    )

# ✅ Actualizar habitación
@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    update_data: RoomUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    room = db.query(Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    if current.role != UserRole.SUPERADMIN and room.residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado para editar esta habitación")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return RoomOut.model_validate(room, from_attributes=True)

# ✅ Eliminar habitación
@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    room = db.query(Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    if current.role != UserRole.SUPERADMIN and room.residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar esta habitación")

    db.delete(room)
    db.commit()
    return {"detail": "Habitación eliminada correctamente"}