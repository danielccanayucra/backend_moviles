from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional

from app.api.deps import get_db, require_role, get_current_user
from app.models.residence import Residence
from app.models.user import UserRole, User
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.models.contract_details import ContractDetails, ContractDetailsStatus
from app.schemas.contract_details import ContractDetailsStatus
from app.schemas.reservation import ReservationCreate, ReservationOut

from sqlalchemy.orm import aliased
router = APIRouter()

# --------------------------------------------------------------------
# 🟢 Crear reserva (solo estudiante o superadmin)
# --------------------------------------------------------------------

@router.post("/", response_model=ReservationOut)
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.STUDENT, UserRole.SUPERADMIN)),
):
    room = db.query(Room).get(data.room_id)
    if not room or not room.is_available:
        raise HTTPException(status_code=404, detail="Habitación no disponible")

    # 🔍 1) Validar si el estudiante ya tiene una reserva activa
    #    (activa = PENDING o CONFIRMED)
    if current.role == UserRole.STUDENT:
        active_statuses = [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
        active_reservation = (
            db.query(Reservation)
            .filter(
                Reservation.student_id == current.id,
                Reservation.status.in_(active_statuses),
            )
            .first()
        )
        if active_reservation:
            raise HTTPException(
                status_code=400,
                detail="Ya tienes una reserva activa. No puedes crear otra.",
            )

    # 🔍 2) Verificar solapamiento de fechas en la habitación (reservas CONFIRMED)
    conflicts = (
        db.query(Reservation)
        .filter(
            Reservation.room_id == data.room_id,
            Reservation.status == ReservationStatus.CONFIRMED,
            or_(
                and_(Reservation.start_date <= data.start_date, Reservation.end_date > data.start_date),
                and_(Reservation.start_date < data.end_date, Reservation.end_date >= data.end_date),
                and_(Reservation.start_date >= data.start_date, Reservation.end_date <= data.end_date),
            ),
        )
        .first()
    )

    if conflicts:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas se solapa con otra reserva confirmada",
        )

    # 3) Crear reserva en estado PENDING
    res = Reservation(
        room_id=data.room_id,
        student_id=current.id if current.role == UserRole.STUDENT else None,
        start_date=data.start_date,
        end_date=data.end_date,
        status=ReservationStatus.PENDING,
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    return ReservationOut(
        id=res.id,
        room_id=res.room_id,
        student_id=res.student_id,
        start_date=res.start_date,
        end_date=res.end_date,
        status=res.status,
    )


# ... existing code ...
@router.post("/{reservation_id}/confirm", response_model=ReservationOut)
def confirm_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    res = db.query(Reservation).get(reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    room = db.query(Room).get(res.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    # Solo el owner de la residencia o un superadmin puede confirmar
    if current.role != UserRole.SUPERADMIN and room.residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Cambiar estado a CONFIRMED
    res.status = ReservationStatus.CONFIRMED

    # Marcar habitación como no disponible
    room.is_available = False

    # Si ya existen detalles para esta reserva, no crear otro
    existing_details = db.query(ContractDetails).filter(
        ContractDetails.reservation_id == res.id
    ).first()

    if not existing_details:
        # Crear ContractDetails pre-llenado y editable
        details = ContractDetails(
            reservation_id=res.id,
            room_id=room.id,
            student_id=res.student_id,
            owner_id=room.residence.owner_id,
            title=f"Contrato de alquiler - {room.title}",
            description=f"Detalles del contrato para la habitación '{room.title}' en la residencia '{room.residence.name}'.",
            monthly_price=room.price_per_month,
            deposit_amount=room.price_per_month,   # Ejemplo: 1 mes de garantía (ajustable en el form)
            payment_day=5,                         # Ejemplo por defecto, editable
            start_date=res.start_date,
            end_date=res.end_date,
            included_services="Agua, luz, internet (ejemplo, editable).",
            rules=(
                "1. El estudiante se compromete a respetar las normas internas de la residencia.\n"
                "2. No se permiten fiestas ruidosas después de las 22:00.\n"
                "3. Mantener la limpieza y el orden de los espacios comunes.\n"
            ),
            extra_conditions="",
            status=ContractDetailsStatus.DRAFT,
        )
        db.add(details)

    db.commit()
    db.refresh(res)

    return ReservationOut(
        id=res.id,
        room_id=res.room_id,
        student_id=res.student_id,
        start_date=res.start_date,
        end_date=res.end_date,
        status=res.status,
    )


@router.post("/{reservation_id}/reject", response_model=ReservationOut)
def reject_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    res = db.query(Reservation).get(reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    room = db.query(Room).get(res.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Habitación no encontrada")

    if current.role != UserRole.SUPERADMIN and room.residence.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    res.status = ReservationStatus.REJECTED
    db.commit()
    db.refresh(res)

    return ReservationOut(
        id=res.id,
        room_id=res.room_id,
        student_id=res.student_id,
        start_date=res.start_date,
        end_date=res.end_date,
        status=res.status,
    )

# --------------------------------------------------------------------
# 📋 Listar todas las reservas (según permisos)
# --------------------------------------------------------------------
@router.get("/", response_model=List[ReservationOut])
def list_reservations(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    status: Optional[ReservationStatus] = None,
    room_id: Optional[int] = None,
):
    owner = aliased(User)
    student = aliased(User)

    q = (
        db.query(
            Reservation.id.label("id"),
            Reservation.room_id.label("room_id"),
            Reservation.student_id.label("student_id"),
            Reservation.start_date.label("start_date"),
            Reservation.end_date.label("end_date"),
            Reservation.status.label("status"),
            Reservation.total_price.label("total_price"),

            owner.full_name.label("owner_name"),
            student.full_name.label("student_name"),
            Residence.name.label("residence_name"),
            Residence.address.label("residence_address"),
            Room.price_per_month.label("room_price"),
        )
        .join(Room, Room.id == Reservation.room_id)
        .join(Residence, Residence.id == Room.residence_id)
        .join(owner, owner.id == Residence.owner_id)
        .join(student, student.id == Reservation.student_id)
    )

    if status:
        q = q.filter(Reservation.status == status)

    if room_id:
        q = q.filter(Reservation.room_id == room_id)

    if current.role == UserRole.STUDENT:
        q = q.filter(Reservation.student_id == current.id)

    q = q.order_by(Reservation.id.desc())
    rows = q.all()

    # 👇 aquí el cambio importante
    return [ReservationOut(**dict(r._mapping)) for r in rows]

# --------------------------------------------------------------------
# 🧑‍🎓 Listar reservas de un estudiante específico (por id)
# --------------------------------------------------------------------
@router.get("/student/{student_id}", response_model=List[ReservationOut])
def list_reservations_by_student(
    student_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.STUDENT, UserRole.SUPERADMIN)),
):
    # Solo el propio estudiante o un superadmin puede verlas
    if current.role != UserRole.SUPERADMIN and current.id != student_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    reservations = db.query(Reservation).filter(Reservation.student_id == student_id).all()
    return [
        ReservationOut(
            id=r.id,
            room_id=r.room_id,
            student_id=r.student_id,
            start_date=r.start_date,
            end_date=r.end_date,
            status=r.status,
        )
        for r in reservations
    ]


# --------------------------------------------------------------------
# 🏠 Listar reservas de un propietario (por id)
# --------------------------------------------------------------------
@router.get("/owner/{owner_id}", response_model=List[ReservationOut])
def list_reservations_by_owner(
    owner_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN))
):
    """
    🔹 Lista todas las reservas asociadas a las habitaciones del owner.
    """

    from app.models.room import Room
    from app.models.residence import Residence

    # 🔸 Buscar habitaciones pertenecientes a residencias del owner
    rooms_subquery = (
        db.query(Room.id)
        .join(Residence, Room.residence_id == Residence.id)
        .filter(Residence.owner_id == owner_id)
        .subquery()
    )

    # 🔸 Traer las reservas asociadas a esas habitaciones
    reservations = (
        db.query(Reservation)
        .filter(Reservation.room_id.in_(rooms_subquery))
        .order_by(Reservation.id.desc())
        .all()
    )

    return [
        ReservationOut(
            id=r.id,
            room_id=r.room_id,
            student_id=r.student_id,
            start_date=r.start_date,
            end_date=r.end_date,
            status=r.status,
        )
        for r in reservations
    ]
# ✅ LISTAR RESERVAS POR OWNER (con datos completos)
@router.get("/by_owner/{owner_id}", response_model=List[ReservationOut])
def list_reservations_by_owner(owner_id: int, db: Session = Depends(get_db)):
    """
    Lista todas las reservas asociadas a las residencias del owner.
    Devuelve datos completos del contrato (propietario, estudiante, residencia, habitación).
    """

    reservations = (
        db.query(Reservation)
        .join(Room, Room.id == Reservation.room_id)
        .join(Residence, Residence.id == Room.residence_id)
        .join(User, User.id == Residence.owner_id)
        .options(joinedload(Reservation.room).joinedload(Room.residence))
        .filter(Residence.owner_id == owner_id)
        .all()
    )

    result = []
    for r in reservations:
        room = r.room
        residence = room.residence if room else None

        student = db.query(User).get(r.student_id) if r.student_id else None
        owner = db.query(User).get(owner_id)

        result.append({
            "id": r.id,
            "room_id": r.room_id,
            "student_id": r.student_id,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "status": r.status,
            "total_price": getattr(r, "total_price", 0.0),

            # ✅ Datos completos para el contrato
            "owner_name": owner.full_name if owner else "No disponible",
            "student_name": student.full_name if student else "No disponible",
            "residence_name": residence.name if residence else "Sin nombre",
            "residence_address": residence.address if residence else "Sin dirección",
            "room_price": room.price_per_month if room else 0.0,
        })

    return result

