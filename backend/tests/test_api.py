import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image as PILImage

from app.db.session import get_db
from app.main import app
from app.models.image import Image, ProcessingStatus


def _make_test_image_bytes() -> bytes:
    img = PILImage.new("RGB", (640, 480), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
@patch("app.api.v1.images.process_image_task")
@patch("app.api.v1.images.save_upload")
async def test_upload_valid_image(mock_save_upload, mock_task):
    mock_image = MagicMock(spec=Image)
    mock_image.id = 1
    mock_image.processing_id = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    mock_image.status = ProcessingStatus.PENDING
    mock_save_upload.return_value = mock_image
    mock_task.delay = MagicMock()

    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            files = {"file": ("test.png", _make_test_image_bytes(), "image/png")}
            response = await client.post("/api/v1/images/upload", files=files)

        assert response.status_code == 202
        data = response.json()
        assert "processing_id" in data
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(1)
        mock_db.commit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_invalid_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = await client.post("/api/v1/images/upload", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_status_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/images/00000000-0000-0000-0000-000000000001/status"
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_results_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/images/00000000-0000-0000-0000-000000000001/results"
        )
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.api.v1.images.get_image_by_processing_id")
async def test_status_completed(mock_get_image):
    mock_image = MagicMock()
    mock_image.processing_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    mock_image.status = ProcessingStatus.COMPLETED
    mock_image.failure_reason = None
    mock_image.processing_start_time = None
    mock_image.processing_completion_time = None
    mock_get_image.return_value = mock_image

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/images/{mock_image.processing_id}/status"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["message"] == "Processing completed successfully"


@pytest.mark.asyncio
@patch("app.api.v1.images.get_image_by_processing_id")
async def test_results_with_analysis(mock_get_image):
    mock_analysis = MagicMock()
    mock_analysis.overall_status = "good"
    mock_analysis.overall_score = 0.9

    mock_image = MagicMock()
    mock_image.processing_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    mock_image.status = ProcessingStatus.COMPLETED
    mock_image.analysis_result = mock_analysis
    mock_get_image.return_value = mock_image

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/images/{mock_image.processing_id}/results"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["analysis"] is not None
