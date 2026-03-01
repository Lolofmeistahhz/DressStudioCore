import logging
import uuid
from pathlib import Path


from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_str(val) -> str:
    """Enum или строка → строка."""
    return val.value if hasattr(val, "value") else str(val)


def media_url(path: str | None) -> str | None:
    """
    /media/abc.jpg  →  https://yourdomain.com/media/abc.jpg
    None или пустая строка → None
    Уже полный URL → возвращаем как есть.
    """
    if not path:
        return None
    if path.startswith("http"):
        return path
    base = settings.BASE_URL.rstrip("/")
    return f"{base}{path}"


async def save_uploaded_file(file) -> str | None:
    if not file or not hasattr(file, "filename") or not file.filename:
        return None
    try:
        ext      = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / filename
        content   = await file.read()
        file_path.write_bytes(content)

        # Возвращаем только путь — media_url() добавит домен при отдаче
        return f"/media/{filename}"
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return None