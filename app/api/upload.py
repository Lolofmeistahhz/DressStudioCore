from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.shared import save_uploaded_file, media_url

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    path = await save_uploaded_file(file)
    if not path:
        raise HTTPException(status_code=400, detail="Не удалось загрузить файл")
    return {"url": media_url(path), "path": path}