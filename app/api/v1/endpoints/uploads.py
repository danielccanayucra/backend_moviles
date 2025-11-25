from fastapi import APIRouter, UploadFile, File, HTTPException
import os, uuid

router = APIRouter()
MEDIA_ROOT = "media"

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo imágenes")
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(MEDIA_ROOT, name)
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"url": f"/{path}"}
