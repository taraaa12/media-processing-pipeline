import pytest

from app.analyzers.dimensions import analyze_dimensions
import numpy as np


def test_dimension_valid():
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    result = analyze_dimensions(img, 640, 480)
    assert result.status == "valid"


def test_dimension_too_small():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = analyze_dimensions(img, 100, 100)
    assert result.status == "invalid"
