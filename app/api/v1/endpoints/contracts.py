from datetime import datetime
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm

from app.api.deps import get_db, require_role, get_current_user
from app.models.user import UserRole, User
from app.models.contract import Contract
from app.models.contract_details import ContractDetails
from app.schemas.contract import ContractOut

router = APIRouter()

# Carpeta donde se van a guardar los PDFs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(BASE_DIR, "generated_contracts")
os.makedirs(PDF_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers para construir el PDF desde ContractDetails
# ---------------------------------------------------------------------------

def _build_contract_story(details: ContractDetails):
    """
    Construye la historia (lista de elementos) para ReportLab
    a partir de los datos de ContractDetails.
    """
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []

    # Título
    story.append(Paragraph(details.title or "Contrato de alquiler", title_style))
    story.append(Spacer(1, 0.5 * cm))

    # Descripción general
    story.append(Paragraph("<b>Descripción:</b> " + (details.description or ""), normal_style))
    story.append(Spacer(1, 0.3 * cm))

    # Fechas y monto
    if details.start_date and details.end_date:
        story.append(Paragraph(
            f"<b>Duración del contrato:</b> "
            f"desde {details.start_date.strftime('%d/%m/%Y')} "
            f"hasta {details.end_date.strftime('%d/%m/%Y')}",
            normal_style,
        ))
        story.append(Spacer(1, 0.2 * cm))

    if details.monthly_price is not None:
        story.append(Paragraph(
            f"<b>Precio mensual:</b> S/ {details.monthly_price:.2f}",
            normal_style,
        ))

    if details.deposit_amount is not None:
        story.append(Paragraph(
            f"<b>Depósito / garantía:</b> S/ {details.deposit_amount:.2f}",
            normal_style,
        ))

    if details.payment_day is not None:
        story.append(Paragraph(
            f"<b>Día de pago cada mes:</b> {details.payment_day}",
            normal_style,
        ))

    story.append(Spacer(1, 0.5 * cm))

    # Servicios incluidos
    story.append(Paragraph("SERVICIOS INCLUIDOS", heading_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(details.included_services or "No especificado.", normal_style))
    story.append(Spacer(1, 0.5 * cm))

    # Reglas / reglamento
    story.append(Paragraph("REGLAS DE LA RESIDENCIA", heading_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(details.rules or "No se han definido reglas adicionales.", normal_style))
    story.append(Spacer(1, 0.5 * cm))

    # Condiciones adicionales
    story.append(Paragraph("CONDICIONES ADICIONALES", heading_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(details.extra_conditions or "Sin condiciones adicionales.", normal_style))
    story.append(Spacer(1, 0.8 * cm))

    # Firmas
    story.append(Paragraph("______________________________", normal_style))
    story.append(Paragraph("Propietario / Representante", normal_style))
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("______________________________", normal_style))
    story.append(Paragraph("Estudiante", normal_style))
    story.append(Spacer(1, 0.8 * cm))

    # Fecha generación
    story.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        normal_style,
    ))

    return story


def _generate_contract_pdf(details: ContractDetails) -> str:
    """
    Genera un PDF a partir de ContractDetails y devuelve la ruta absoluta del archivo.
    """
    filename = f"contract_reservation_{details.reservation_id}_details_{details.id}.pdf"
    output_path = os.path.join(PDF_DIR, filename)

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = _build_contract_story(details)
    doc.build(story)

    return output_path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate-from-details/{details_id}", response_model=ContractOut)
def generate_contract_from_details(
    details_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.OWNER, UserRole.SUPERADMIN)),
):
    """
    Genera un PDF a partir de ContractDetails y crea un registro en la tabla Contract.
    """
    details = db.query(ContractDetails).get(details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    # Solo el owner asociado o superadmin puede generar
    if current.role != UserRole.SUPERADMIN and details.owner_id != current.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Opcional: evitar duplicar contratos para los mismos detalles
    existing_contract = (
        db.query(Contract)
        .filter(Contract.details_id == details.id)
        .first()
    )
    if existing_contract:
        raise HTTPException(status_code=400, detail="Ya existe un contrato para estos detalles")

    # Generar PDF
    pdf_path = _generate_contract_pdf(details)
    filename = os.path.basename(pdf_path)

    pdf_url = f"/generated_contracts/{filename}"

    # Guardar en tabla Contract (ahora con details_id)
    contract = Contract(
        reservation_id=details.reservation_id,
        details_id=details.id,  # 🔹 importante
        pdf_url=pdf_url,
        created_at=datetime.utcnow(),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return contract

@router.put("/{contract_id}/regenerate-from-details", response_model=ContractOut)
def regenerate_contract_pdf_from_details(
    contract_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Regenera el PDF de un contrato usando sus ContractDetails:
    - SUPERADMIN: cualquiera.
    - OWNER: solo si es el owner de esos details.
    - STUDENT: no puede regenerar.
    """
    contract = db.query(Contract).get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    details = db.query(ContractDetails).get(contract.details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    # Permisos
    if current.role != UserRole.SUPERADMIN:
        # Debe estar asociado a esos detalles
        if current.id not in [details.owner_id, details.student_id]:
            raise HTTPException(status_code=403, detail="No autorizado")
        # Solo owner puede regenerar
        if current.id != details.owner_id:
            raise HTTPException(status_code=403, detail="Solo el propietario puede regenerar el contrato")

    # Usar el mismo filename si ya existe, para reemplazar el PDF
    if contract.pdf_url:
        filename = os.path.basename(contract.pdf_url)
    else:
        filename = f"contract_reservation_{details.reservation_id}_details_{details.id}.pdf"

    output_path = os.path.join(PDF_DIR, filename)
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = _build_contract_story(details)
    doc.build(story)

    contract.pdf_url = f"/generated_contracts/{filename}"
    db.commit()
    db.refresh(contract)

    return contract

@router.get("/", response_model=List[ContractOut])
def list_contracts(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    Lista contratos:
    - SUPERADMIN: todos.
    - OWNER: solo contratos de sus reservas.
    - STUDENT: solo contratos de sus reservas.
    """
    query = db.query(Contract)

    if current.role == UserRole.SUPERADMIN:
        contracts = query.order_by(Contract.created_at.desc()).all()
        return contracts

    # Para OWNER y STUDENT filtramos por reservation/contract_details
    contracts = (
        query.join(ContractDetails, Contract.reservation_id == ContractDetails.reservation_id)
        .filter(
            (ContractDetails.owner_id == current.id)
            if current.role == UserRole.OWNER
            else (ContractDetails.student_id == current.id)
        )
        .order_by(Contract.created_at.desc())
        .all()
    )
    return contracts

# ... existing code ...

@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    contract = db.query(Contract).get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    details = db.query(ContractDetails).get(contract.details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    if current.role != UserRole.SUPERADMIN and current.id not in [details.owner_id, details.student_id]:
        raise HTTPException(status_code=403, detail="No autorizado")

    return contract

# ... existing code ...

@router.get("/{contract_id}/download")
def download_contract_pdf(
    contract_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    SUPERADMIN: descarga cualquiera.
    OWNER / STUDENT: solo si están asociados en los ContractDetails.
    """
    contract = db.query(Contract).get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    details = db.query(ContractDetails).get(contract.details_id)
    if not details:
        raise HTTPException(status_code=404, detail="Detalles de contrato no encontrados")

    if current.role != UserRole.SUPERADMIN and current.id not in [details.owner_id, details.student_id]:
        raise HTTPException(status_code=403, detail="No autorizado")

    rel_path = contract.pdf_url.lstrip("/")
    pdf_path = os.path.join(BASE_DIR, rel_path)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )

@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """
    Elimina:
    - El registro Contract.
    - El archivo PDF asociado.
    - Los ContractDetails asociados (opcional, según reglas).
    Solo SUPERADMIN.
    """
    contract = db.query(Contract).get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    # Eliminar archivo físico si existe
    if contract.pdf_url:
        rel_path = contract.pdf_url.lstrip("/")
        pdf_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    # Obtener details por reservation_id (según diseño actual)
    details = (
        db.query(ContractDetails)
        .filter(ContractDetails.reservation_id == contract.reservation_id)
        .first()
    )

    if details:
        db.delete(details)

    db.delete(contract)
    db.commit()
    return