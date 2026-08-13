import hashlib
import uuid
from unittest.mock import MagicMock

from app.analyzers.duplicate import analyze_duplicate
from app.utils.file_utils import compute_sha256


def test_sha256_consistency():
    data = b"test image content"
    h1 = compute_sha256(data)
    h2 = hashlib.sha256(data).hexdigest()
    assert h1 == h2
    assert len(h1) == 64


def test_different_content_different_hash():
    assert compute_sha256(b"a") != compute_sha256(b"b")


def _mock_db_exact_match(match_image):
    """Mock db for exact SHA-256 duplicate lookup."""
    exact_result = MagicMock()
    exact_result.scalar_one_or_none.return_value = match_image

    perceptual_result = MagicMock()
    perceptual_result.scalars.return_value.all.return_value = []

    mock_db = MagicMock()
    mock_db.execute.side_effect = [exact_result, perceptual_result]
    return mock_db


def _mock_db_no_match():
    exact_result = MagicMock()
    exact_result.scalar_one_or_none.return_value = None

    perceptual_result = MagicMock()
    perceptual_result.scalars.return_value.all.return_value = []

    mock_db = MagicMock()
    mock_db.execute.side_effect = [exact_result, perceptual_result]
    return mock_db


def test_analyze_duplicate_exact_match():
    original_id = uuid.uuid4()
    match_image = MagicMock()
    match_image.processing_id = original_id

    mock_db = _mock_db_exact_match(match_image)
    result = analyze_duplicate(mock_db, "abc123hash", None, str(uuid.uuid4()))

    assert result.status == "duplicate"
    assert result.confidence >= 0.99
    assert result.details["match_type"] == "exact_sha256"
    assert result.details["original_processing_id"] == str(original_id)
    assert result.issue is not None


def test_analyze_duplicate_unique():
    mock_db = _mock_db_no_match()
    result = analyze_duplicate(mock_db, "uniquehash", "phash123", str(uuid.uuid4()))

    assert result.status == "unique"
    assert result.issue is None
    assert result.details["match_type"] is None


def test_analyze_duplicate_perceptual_match():
    original_id = uuid.uuid4()
    similar_image = MagicMock()
    similar_image.processing_id = original_id
    similar_image.perceptual_hash = "0000000000000000"

    exact_result = MagicMock()
    exact_result.scalar_one_or_none.return_value = None

    perceptual_result = MagicMock()
    perceptual_result.scalars.return_value.all.return_value = [similar_image]

    mock_db = MagicMock()
    mock_db.execute.side_effect = [exact_result, perceptual_result]

    result = analyze_duplicate(mock_db, "uniquehash", "0000000000000000", str(uuid.uuid4()))

    assert result.status == "likely_duplicate"
    assert result.details["match_type"] == "perceptual_hash"
    assert result.details["original_processing_id"] == str(original_id)
