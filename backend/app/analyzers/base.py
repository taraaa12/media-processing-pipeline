from dataclasses import dataclass
from typing import Any


@dataclass
class AnalyzerResult:
    name: str
    score: float | None = None
    status: str | None = None
    confidence: float = 0.5
    details: dict[str, Any] | None = None
    issue: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "status": self.status,
            "confidence": self.confidence,
            "details": self.details or {},
            "issue": self.issue,
        }
