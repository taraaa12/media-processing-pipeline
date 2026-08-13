import pytest

from app.utils.vehicle_number import (
    extract_vehicle_candidates,
    normalize_vehicle_text,
    validate_indian_vehicle_number,
)


@pytest.mark.parametrize(
    "raw,expected_valid",
    [
        ("KA01AB1234", True),
        ("KA 01 AB 1234", True),
        ("KA-01-AB-1234", True),
        ("INVALID123", False),
        ("", False),
    ],
)
def test_vehicle_number_validation(raw: str, expected_valid: bool):
    is_valid, normalized, confidence = validate_indian_vehicle_number(raw)
    assert is_valid == expected_valid
    if expected_valid:
        assert normalized is not None
        assert confidence > 0.5


def test_normalize_vehicle_text():
    assert normalize_vehicle_text("KA 01 AB 1234") == "KA01AB1234"


def test_extract_vehicle_candidates():
    text = "Vehicle KA01AB1234 parked near gate"
    candidates = extract_vehicle_candidates(text)
    assert "KA01AB1234" in candidates
