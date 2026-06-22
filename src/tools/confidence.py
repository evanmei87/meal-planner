from dataclasses import dataclass


HIGH_CONFIDENCE_THRESHOLD = 0.7
REVIEW_CONFIDENCE_THRESHOLD = 0.4


@dataclass
class ConfidenceResult:
    score: float
    level: str
    should_auto_save: bool
    reason: str | None = None


def classify_confidence(score: float, high_threshold: float = 0.7, review_threshold: float = 0.4) -> ConfidenceResult:
    if score >= high_threshold:
        return ConfidenceResult(score=score, level="high", should_auto_save=True, reason="Auto-save eligible")
    if score >= review_threshold:
        return ConfidenceResult(score=score, level="review", should_auto_save=False, reason="Requires user confirmation")
    return ConfidenceResult(score=score, level="low", should_auto_save=False, reason="Requires manual macro entry")


def format_confidence(score: float) -> str:
    return f"{score:.2f}"
