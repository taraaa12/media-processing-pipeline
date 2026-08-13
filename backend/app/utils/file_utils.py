import hashlib
import re
import uuid
from pathlib import Path

from PIL import Image as PILImage

from app.core.config import settings


def generate_processing_id() -> uuid.UUID:
    return uuid.uuid4()


def generate_stored_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_join_upload_dir(stored_filename: str) -> Path:
    upload_root = Path(settings.upload_dir).resolve()
    target = (upload_root / stored_filename).resolve()
    if not str(target).startswith(str(upload_root)):
        raise ValueError("Invalid file path")
    return target


def get_image_dimensions(file_path: Path) -> tuple[int, int]:
    with PILImage.open(file_path) as img:
        return img.size


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extension_set:
        raise ValueError(f"Extension '.{ext}' not allowed")
    return ext


MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def guess_mime_from_extension(ext: str) -> str:
    return MIME_MAP.get(ext.lower(), "application/octet-stream")


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^\w.\-]", "_", name)[:255]
