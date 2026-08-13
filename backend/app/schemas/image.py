from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    processing_id: UUID
    status: str
    message: str


class ImageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    processing_id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    width: int | None
    height: int | None
    status: str
    upload_time: datetime
    processing_start_time: datetime | None = None
    processing_completion_time: datetime | None = None
    failure_reason: str | None = None


class AnalysisResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    blur_score: float | None = None
    blur_status: str | None = None
    blur_confidence: float | None = None
    brightness_score: float | None = None
    brightness_status: str | None = None
    brightness_confidence: float | None = None
    is_duplicate: bool = False
    duplicate_original_processing_id: str | None = None
    duplicate_confidence: float | None = None
    duplicate_match_type: str | None = None
    ocr_raw_text: str | None = None
    ocr_cleaned_text: str | None = None
    vehicle_number: str | None = None
    vehicle_number_valid: bool | None = None
    ocr_confidence: float | None = None
    screenshot_probability: float | None = None
    screenshot_confidence: float | None = None
    screenshot_signals: dict[str, Any] | None = None
    tampering_probability: float | None = None
    tampering_confidence: float | None = None
    tampering_signals: dict[str, Any] | None = None
    dimension_valid: bool | None = None
    dimension_details: dict[str, Any] | None = None
    overall_score: float | None = None
    overall_status: str | None = None
    overall_confidence: float | None = None
    detected_issues: list[str] | None = None
    analyzer_details: dict[str, Any] | None = None


class ImageDetailResponse(ImageBase):
    sha256_hash: str
    analysis_result: AnalysisResultSchema | None = None


class StatusResponse(BaseModel):
    processing_id: UUID
    status: str
    message: str | None = None
    processing_start_time: datetime | None = None
    processing_completion_time: datetime | None = None


class ResultsResponse(BaseModel):
    processing_id: UUID
    status: str
    analysis: AnalysisResultSchema | None = None


class FailureResponse(BaseModel):
    processing_id: UUID
    status: str
    failure_reason: str | None = None


class ImageListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    processing_id: UUID
    original_filename: str
    status: str
    upload_time: datetime
    overall_status: str | None = None
    overall_confidence: float | None = None
    thumbnail_url: str | None = None


class PaginatedImageList(BaseModel):
    items: list[ImageListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DashboardStats(BaseModel):
    total_uploads: int
    pending: int
    processing: int
    completed: int
    failed: int
    good: int
    needs_review: int
    poor: int
    average_processing_time_seconds: float | None = None


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
