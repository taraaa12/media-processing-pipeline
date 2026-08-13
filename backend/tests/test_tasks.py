import uuid
from unittest.mock import MagicMock, patch

from celery.exceptions import Retry

from app.models.image import Image, ProcessingStatus
from app.workers.tasks import process_image_task, _retry_countdown


def test_retry_countdown_increases():
    assert _retry_countdown(0) == 10
    assert _retry_countdown(1) == 20
    assert _retry_countdown(10) == 120


@patch("app.workers.tasks.run_full_analysis")
@patch("app.workers.tasks.SyncSessionLocal")
def test_task_success(mock_session_local, mock_analysis):
    mock_analysis.return_value = MagicMock()

    mock_db = MagicMock()
    mock_image = MagicMock(spec=Image)
    mock_image.id = 1
    mock_image.status = ProcessingStatus.PENDING
    mock_image.processing_id = uuid.uuid4()
    mock_db.get.return_value = mock_image
    mock_session_local.return_value = mock_db

    result = process_image_task.run(1)

    assert result["status"] == "completed"
    assert mock_image.status == ProcessingStatus.COMPLETED


@patch("app.workers.tasks.run_full_analysis")
@patch("app.workers.tasks.SyncSessionLocal")
def test_task_retry_keeps_processing(mock_session_local, mock_analysis):
    mock_analysis.side_effect = RuntimeError("transient error")

    mock_db = MagicMock()
    mock_image = MagicMock(spec=Image)
    mock_image.id = 2
    mock_image.status = ProcessingStatus.PENDING
    mock_image.processing_id = uuid.uuid4()
    mock_db.get.return_value = mock_image
    mock_session_local.return_value = mock_db

    process_image_task.push_request(retries=0)
    with patch.object(process_image_task, "retry", side_effect=Retry()):
        try:
            process_image_task.run(2)
        except Retry:
            pass

    assert mock_image.status == ProcessingStatus.PROCESSING
    assert mock_image.failure_reason is not None
    assert "Retry" in mock_image.failure_reason


@patch("app.workers.tasks.run_full_analysis")
@patch("app.workers.tasks.SyncSessionLocal")
def test_task_final_failure(mock_session_local, mock_analysis):
    mock_analysis.side_effect = RuntimeError("permanent error")

    mock_db = MagicMock()
    mock_image = MagicMock(spec=Image)
    mock_image.id = 3
    mock_image.status = ProcessingStatus.PROCESSING
    mock_image.processing_id = uuid.uuid4()
    mock_db.get.return_value = mock_image
    mock_session_local.return_value = mock_db

    process_image_task.push_request(retries=3)
    result = process_image_task.run(3)

    assert result["status"] == "failed"
    assert mock_image.status == ProcessingStatus.FAILED
    assert mock_image.processing_completion_time is not None


@patch("app.workers.tasks.run_full_analysis")
@patch("app.workers.tasks.SyncSessionLocal")
def test_task_already_completed(mock_session_local, mock_analysis):
    mock_db = MagicMock()
    mock_image = MagicMock(spec=Image)
    mock_image.status = ProcessingStatus.COMPLETED
    mock_db.get.return_value = mock_image
    mock_session_local.return_value = mock_db

    result = process_image_task.run(4)

    assert result["status"] == "already_completed"
    mock_analysis.assert_not_called()
