import math
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.image import AnalysisResult, Image, OverallStatus, ProcessingStatus
from app.schemas.image import DashboardStats, ImageListItem, PaginatedImageList


async def list_images(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    overall_status: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = "upload_time",
    sort_order: str = "desc",
) -> PaginatedImageList:
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    query = select(Image).options(selectinload(Image.analysis_result))

    if status:
        try:
            query = query.where(Image.status == ProcessingStatus(status))
        except ValueError:
            pass

    if overall_status:
        try:
            query = query.join(AnalysisResult, isouter=True).where(
                AnalysisResult.overall_status == OverallStatus(overall_status)
            )
        except ValueError:
            pass

    if search:
        pattern = f"%{search}%"
        query = query.where(
            (Image.original_filename.ilike(pattern)) | (Image.processing_id.cast(str).ilike(pattern))
        )

    if date_from:
        query = query.where(Image.upload_time >= date_from)
    if date_to:
        query = query.where(Image.upload_time <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    sort_column = getattr(Image, sort_by, Image.upload_time)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    images = result.scalars().unique().all()

    items = []
    for img in images:
        ar = img.analysis_result
        items.append(
            ImageListItem(
                processing_id=img.processing_id,
                original_filename=img.original_filename,
                status=img.status.value,
                upload_time=img.upload_time,
                overall_status=ar.overall_status.value if ar and ar.overall_status else None,
                overall_confidence=ar.overall_confidence if ar else None,
                thumbnail_url=f"/api/v1/images/{img.processing_id}/file",
            )
        )

    total_pages = math.ceil(total / page_size) if page_size else 1
    return PaginatedImageList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    total = (await db.execute(select(func.count(Image.id)))).scalar() or 0
    pending = (
        await db.execute(select(func.count(Image.id)).where(Image.status == ProcessingStatus.PENDING))
    ).scalar() or 0
    processing = (
        await db.execute(select(func.count(Image.id)).where(Image.status == ProcessingStatus.PROCESSING))
    ).scalar() or 0
    completed = (
        await db.execute(select(func.count(Image.id)).where(Image.status == ProcessingStatus.COMPLETED))
    ).scalar() or 0
    failed = (
        await db.execute(select(func.count(Image.id)).where(Image.status == ProcessingStatus.FAILED))
    ).scalar() or 0

    good = (
        await db.execute(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.overall_status == OverallStatus.GOOD)
        )
    ).scalar() or 0
    needs_review = (
        await db.execute(
            select(func.count(AnalysisResult.id)).where(
                AnalysisResult.overall_status == OverallStatus.NEEDS_REVIEW
            )
        )
    ).scalar() or 0
    poor = (
        await db.execute(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.overall_status == OverallStatus.POOR)
        )
    ).scalar() or 0

    avg_time_result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    Image.processing_completion_time - Image.processing_start_time,
                )
            )
        ).where(Image.status == ProcessingStatus.COMPLETED)
    )
    avg_time = avg_time_result.scalar()

    return DashboardStats(
        total_uploads=total,
        pending=pending,
        processing=processing,
        completed=completed,
        failed=failed,
        good=good,
        needs_review=needs_review,
        poor=poor,
        average_processing_time_seconds=round(float(avg_time), 2) if avg_time else None,
    )
