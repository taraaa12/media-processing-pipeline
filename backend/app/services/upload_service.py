import io
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import logger
from app.models.image import Image, ProcessingStatus
from app.utils.file_utils import (
    ALLOWED_MIME_TYPES,
    compute_sha256,
    generate_processing_id,
    generate_stored_filename,
    get_image_dimensions,
    safe_join_upload_dir,
    sanitize_filename,
    validate_extension,
)


async def save_upload(db: AsyncSession, file: UploadFile) -> Image:
    if not file.filename:
        raise AppError("No file provided", status_code=400, code="missing_file")

    original_filename = sanitize_filename(file.filename)
    try:
        validate_extension(original_filename)
    except ValueError as exc:
        raise AppError(str(exc), status_code=400, code="invalid_extension") from exc

    content = await file.read()
    if not content:
        raise AppError("Empty file", status_code=400, code="empty_file")

    if len(content) > settings.max_upload_size_bytes:
        raise AppError(
            f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
            status_code=413,
            code="file_too_large",
        )

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise AppError(f"Invalid MIME type: {mime_type}", status_code=400, code="invalid_mime")

    # Validate image can be decoded
    try:
        with PILImage.open(io.BytesIO(content)) as img:
            img.verify()
        with PILImage.open(io.BytesIO(content)) as img:
            width, height = img.size
            if width < 1 or height < 1:
                raise ValueError("Invalid dimensions")
    except Exception as exc:
        raise AppError("Invalid or corrupted image file", status_code=400, code="invalid_image") from exc

    processing_id = generate_processing_id()
    stored_filename = generate_stored_filename(original_filename)
    file_path = safe_join_upload_dir(stored_filename)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path.write_bytes(content)
    sha256_hash = compute_sha256(content)

    image = Image(
        processing_id=processing_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=mime_type,
        file_size=len(content),
        width=width,
        height=height,
        sha256_hash=sha256_hash,
        status=ProcessingStatus.PENDING,
    )
    db.add(image)
    await db.flush()
    await db.refresh(image)

    logger.info("Image uploaded: processing_id=%s filename=%s", processing_id, original_filename)
    return image


async def get_image_by_processing_id(db: AsyncSession, processing_id: UUID) -> Image | None:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Image)
        .options(selectinload(Image.analysis_result))
        .where(Image.processing_id == processing_id)
    )
    return result.scalar_one_or_none()
