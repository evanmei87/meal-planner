import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.confidence import (
    ConfidenceResult,
    classify_confidence,
    format_confidence,
    HIGH_CONFIDENCE_THRESHOLD,
    REVIEW_CONFIDENCE_THRESHOLD,
)


def test_default_thresholds():
    assert HIGH_CONFIDENCE_THRESHOLD == 0.7
    assert REVIEW_CONFIDENCE_THRESHOLD == 0.4


def test_classify_high_confidence():
    result = classify_confidence(0.85)
    assert result.level == "high"
    assert result.should_auto_save is True


def test_classify_review_confidence():
    result = classify_confidence(0.55)
    assert result.level == "review"
    assert result.should_auto_save is False


def test_classify_low_confidence():
    result = classify_confidence(0.2)
    assert result.level == "low"
    assert result.should_auto_save is False


def test_classify_boundary_high():
    result = classify_confidence(0.7)
    assert result.level == "high"


def test_classify_boundary_review():
    result = classify_confidence(0.4)
    assert result.level == "review"


def test_custom_thresholds():
    result = classify_confidence(0.6, high_threshold=0.8, review_threshold=0.5)
    assert result.level == "review"
    assert result.should_auto_save is False


def test_format_confidence():
    assert format_confidence(0.83) == "0.83"
    assert format_confidence(0.1) == "0.10"
    assert format_confidence(1.0) == "1.00"
