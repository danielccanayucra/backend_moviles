from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role
from app.models.contract_details import ContractDetails
from app.models.user import UserRole
from app.schemas.contract_details import (
    ContractDetailsOut,
    ContractDetailsUpdate,
)

router = APIRouter()

@router.get("/by-reservation/{reservation_id}", response_model=ContractDetailsOut)
def get_contract_details_by_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    details = (
        db.query(ContractDetails)
        .filter(ContractDetails.reservation_id == reservation_id)
        .first()
    )
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    # Solo superadmin, owner involucrado o estudiante involucrado
    if (
        current.role != UserRole.SUPERADMIN
        and current.id not in [details.owner_id, details.student_id]
    ):
        raise HTTPException(status_code=403, detail="No autorizado")

    return ContractDetailsOut.model_validate(details, from_attributes=True)


@router.put("/{details_id}", response_model=ContractDetailsOut)
def update_contract_details(
    details_id: int,
    data: ContractDetailsUpdate,
    db: Session = Depends(get_db),
    current = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    details = db.query(ContractDetails).get(details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    if current.role != UserRole.SUPERADMIN and details.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(details, field, value)

    db.commit()
    db.refresh(details)
    return ContractDetailsOut.model_validate(details, from_attributes=True)

@router.get("/{details_id}", response_model=ContractDetailsOut)
def get_contract_details_by_id(
    details_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
):
    details = db.query(ContractDetails).get(details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    # Solo superadmin, owner involucrado o estudiante involucrado
    if (
        current.role != UserRole.SUPERADMIN
        and current.id not in [details.owner_id, details.student_id]
    ):
        raise HTTPException(status_code=403, detail="No autorizado")

    return ContractDetailsOut.model_validate(details, from_attributes=True)
