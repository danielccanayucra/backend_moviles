import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.main import app  # si necesitas la app, opcional

router = APIRouter()

MEDIA_ROOT = "media"  # esta carpeta ya la montas en main.py con StaticFiles

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")

    # Extensión del archivo
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    # Nombre único
    name = f"{uuid.uuid4().hex}{ext}"

    # Ruta física donde se guardará
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    file_path = os.path.join(MEDIA_ROOT, name)

    # Guardar el archivo en disco
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # URL pública (FastAPI sirve /media desde MEDIA_ROOT)
    url = f"/media/{name}"

    return {"url": url}