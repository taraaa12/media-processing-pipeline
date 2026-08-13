import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image as PILImage


@pytest.fixture
def sample_sharp_image(tmp_path: Path) -> Path:
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    # Add sharp edges
    img[50:350, 100:500] = [200, 200, 200]
    img[100:300, 150:450] = [50, 50, 50]
    path = tmp_path / "sharp.png"
    PILImage.fromarray(img).save(path)
    return path


@pytest.fixture
def sample_blurry_image(tmp_path: Path) -> Path:
    img = np.random.randint(100, 150, (400, 600, 3), dtype=np.uint8)
    path = tmp_path / "blurry.png"
    PILImage.fromarray(img).save(path)
    return path


@pytest.fixture
def sample_dark_image(tmp_path: Path) -> Path:
    img = np.full((400, 600, 3), 20, dtype=np.uint8)
    path = tmp_path / "dark.png"
    PILImage.fromarray(img).save(path)
    return path
