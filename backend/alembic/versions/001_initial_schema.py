"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    processing_status = postgresql.ENUM(
        "pending", "processing", "completed", "failed", name="processing_status", create_type=True
    )
    overall_status = postgresql.ENUM(
        "good", "needs_review", "poor", "failed", name="overall_status", create_type=True
    )

    op.create_table(
        "images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("processing_id", sa.UUID(), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("stored_filename", sa.String(length=512), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("perceptual_hash", sa.String(length=64), nullable=True),
        sa.Column("status", processing_status, nullable=False),
        sa.Column("upload_time", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processing_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completion_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("processing_id"),
    )
    op.create_index("ix_images_processing_id", "images", ["processing_id"])
    op.create_index("ix_images_sha256_hash", "images", ["sha256_hash"])
    op.create_index("ix_images_status", "images", ["status"])
    op.create_index("ix_images_perceptual_hash", "images", ["perceptual_hash"])
    op.create_index("ix_images_status_upload_time", "images", ["status", "upload_time"])
    op.create_index("ix_images_upload_time", "images", ["upload_time"])

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("image_id", sa.Integer(), nullable=False),
        sa.Column("blur_score", sa.Float(), nullable=True),
        sa.Column("blur_status", sa.String(length=32), nullable=True),
        sa.Column("blur_confidence", sa.Float(), nullable=True),
        sa.Column("brightness_score", sa.Float(), nullable=True),
        sa.Column("brightness_status", sa.String(length=32), nullable=True),
        sa.Column("brightness_confidence", sa.Float(), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("duplicate_original_processing_id", sa.String(length=36), nullable=True),
        sa.Column("duplicate_confidence", sa.Float(), nullable=True),
        sa.Column("duplicate_match_type", sa.String(length=32), nullable=True),
        sa.Column("ocr_raw_text", sa.Text(), nullable=True),
        sa.Column("ocr_cleaned_text", sa.Text(), nullable=True),
        sa.Column("vehicle_number", sa.String(length=32), nullable=True),
        sa.Column("vehicle_number_valid", sa.Boolean(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("screenshot_probability", sa.Float(), nullable=True),
        sa.Column("screenshot_confidence", sa.Float(), nullable=True),
        sa.Column("screenshot_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tampering_probability", sa.Float(), nullable=True),
        sa.Column("tampering_confidence", sa.Float(), nullable=True),
        sa.Column("tampering_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dimension_valid", sa.Boolean(), nullable=True),
        sa.Column("dimension_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("overall_status", overall_status, nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("detected_issues", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("analyzer_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_id"),
    )


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("images")
    op.execute("DROP TYPE IF EXISTS processing_status")
    op.execute("DROP TYPE IF EXISTS overall_status")
