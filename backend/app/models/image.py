import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OverallStatus(str, enum.Enum):
    GOOD = "good"
    NEEDS_REVIEW = "needs_review"
    POOR = "poor"
    FAILED = "failed"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    perceptual_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True,
    )
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processing_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completion_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    analysis_result: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult", back_populates="image", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_images_status_upload_time", "status", "upload_time"),
        Index("ix_images_upload_time", "upload_time"),
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), unique=True, nullable=False)

    blur_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    blur_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    blur_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    brightness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    brightness_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    brightness_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_original_processing_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    duplicate_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duplicate_match_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    ocr_raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vehicle_number_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    screenshot_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    screenshot_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    screenshot_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    tampering_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    tampering_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    tampering_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    dimension_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dimension_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_status: Mapped[OverallStatus | None] = mapped_column(
        Enum(OverallStatus, name="overall_status", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    detected_issues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    analyzer_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    image: Mapped["Image"] = relationship("Image", back_populates="analysis_result")
