import logging
import uuid
from pathlib import Path

import httpx
from requests import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_str(val) -> str:
    """Enum или строка → строка."""
    return val.value if hasattr(val, "value") else str(val)


async def save_uploaded_file(file) -> str | None:
    if not file or not hasattr(file, 'filename') or not file.filename:
        return None

    try:
        if '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
        else:
            ext = 'jpg'

        filename = f"{uuid.uuid4().hex}.{ext}"

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / filename
        content = await file.read()
        file_path.write_bytes(content)

        # ВАЖНО: возвращаем ТОЛЬКО URL префикс
        return f"/media/{filename}"

    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return None