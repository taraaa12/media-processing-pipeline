from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, not_found
from app.db.session import get_db
from app.schemas.image import (
    DashboardStats,
    FailureResponse,
    ImageDetailResponse,
    PaginatedImageList,
    ResultsResponse,
    StatusResponse,
    UploadResponse,
)
from app.services.image_service import get_dashboard_stats, list_images
from app.services.upload_service import get_image_by_processing_id, save_upload
from app.workers.tasks import process_image_task

router = APIRouter(prefix="/api/v1/images", tags=["images"])


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    try:
        image = await save_upload(db, file)
        await db.commit()
        process_image_task.delay(image.id)
        return UploadResponse(
            processing_id=image.processing_id,
            status=image.status.value,
            message="Image accepted for processing",
        )
    except AppError:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process upload") from exc


@router.get("", response_model=PaginatedImageList)
async def get_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    overall_status: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query("upload_time"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedImageList:
    return await list_images(
        db,
        page,
        page_size,
        status,
        overall_status,
        search,
        date_from,
        date_to,
        sort_by,
        sort_order,
    )


@router.get("/stats/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    return await get_dashboard_stats(db)


@router.get("/{processing_id}", response_model=ImageDetailResponse)
async def get_image(
    processing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ImageDetailResponse:
    image = await get_image_by_processing_id(db, processing_id)
    if not image:
        raise not_found(str(processing_id))
    return ImageDetailResponse.model_validate(image)


@router.get("/{processing_id}/status", response_model=StatusResponse)
async def get_status(
    processing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StatusResponse:
    image = await get_image_by_processing_id(db, processing_id)
    if not image:
        raise not_found(str(processing_id))
    message = None
    if image.status.value == "failed":
        message = image.failure_reason
    elif image.status.value == "completed":
        message = "Processing completed successfully"
    return StatusResponse(
        processing_id=image.processing_id,
        status=image.status.value,
        message=message,
        processing_start_time=image.processing_start_time,
        processing_completion_time=image.processing_completion_time,
    )


@router.get("/{processing_id}/results", response_model=ResultsResponse)
async def get_results(
    processing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResultsResponse:
    image = await get_image_by_processing_id(db, processing_id)
    if not image:
        raise not_found(str(processing_id))
    return ResultsResponse(
        processing_id=image.processing_id,
        status=image.status.value,
        analysis=image.analysis_result,
    )


@router.get("/{processing_id}/failure", response_model=FailureResponse)
async def get_failure(
    processing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FailureResponse:
    image = await get_image_by_processing_id(db, processing_id)
    if not image:
        raise not_found(str(processing_id))
    if image.status.value != "failed":
        raise HTTPException(status_code=400, detail="Image processing has not failed")
    return FailureResponse(
        processing_id=image.processing_id,
        status=image.status.value,
        failure_reason=image.failure_reason,
    )


@router.get("/{processing_id}/file")
async def get_image_file(
    processing_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    image = await get_image_by_processing_id(db, processing_id)
    if not image:
        raise not_found(str(processing_id))
    return FileResponse(
        path=image.file_path,
        media_type=image.mime_type,
        filename=image.original_filename,
    )
