import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.models.image import ProcessingStatus


@pytest.mark.asyncio
async def test_failure_endpoint_not_failed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/images/00000000-0000-0000-0000-000000000001/failure"
        )
    assert response.status_code in (404, 400)


@pytest.mark.asyncio
@patch("app.api.v1.images.get_image_by_processing_id")
async def test_failure_endpoint_failed(mock_get_image):
    mock_image = MagicMock()
    mock_image.processing_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    mock_image.status = ProcessingStatus.FAILED
    mock_image.failure_reason = "Image load failed"
    mock_get_image.return_value = mock_image

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/images/{mock_image.processing_id}/failure"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["failure_reason"] == "Image load failed"
