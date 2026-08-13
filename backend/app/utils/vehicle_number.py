import re

# Indian state/UT codes for vehicle registration
INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "GA", "GJ", "HP", "HR", "JH",
    "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB",
    "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB",
}

# Standard format: XX00XX0000 (2 letters state, 2 digits district, 1-3 letters series, 4 digits)
VEHICLE_NUMBER_PATTERN = re.compile(
    r"^([A-Z]{2})[\s\-]?(\d{1,2})[\s\-]?([A-Z]{1,3})[\s\-]?(\d{4})$",
    re.IGNORECASE,
)

# BH series (Bharat series)
BH_SERIES_PATTERN = re.compile(r"^(\d{2})[\s\-]?BH[\s\-]?(\d{4})[\s\-]?([A-Z]{2})$", re.IGNORECASE)


def normalize_vehicle_text(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text.upper())
    return cleaned


def extract_vehicle_candidates(text: str) -> list[str]:
    if not text:
        return []
    upper = text.upper()
    candidates: list[str] = []
    # Find contiguous alphanumeric sequences that might be plates
    for match in re.finditer(r"[A-Z]{2}[\s\-]?\d{1,2}[\s\-]?[A-Z]{1,3}[\s\-]?\d{4}", upper):
        candidates.append(normalize_vehicle_text(match.group()))
    for match in re.finditer(r"\d{2}[\s\-]?BH[\s\-]?\d{4}[\s\-]?[A-Z]{2}", upper):
        candidates.append(normalize_vehicle_text(match.group()))
    return list(dict.fromkeys(candidates))


def validate_indian_vehicle_number(number: str) -> tuple[bool, str | None, float]:
    """Validate format only. Returns (is_valid, normalized_number, confidence)."""
    if not number:
        return False, None, 0.0

    normalized = normalize_vehicle_text(number)
    if not normalized:
        return False, None, 0.0

    match = re.match(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{4})$", normalized)
    if match:
        state = match.group(1)
        if state in INDIAN_STATE_CODES:
            return True, normalized, 0.85
        return False, normalized, 0.4

    bh_match = BH_SERIES_PATTERN.match(number.upper().replace(" ", ""))
    if bh_match:
        return True, normalize_vehicle_text(number), 0.8

    return False, normalized, 0.2
