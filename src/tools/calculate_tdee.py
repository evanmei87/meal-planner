import json
import os
from pathlib import Path
import csv


def get_user_stats() -> dict:
    """Load user stats from user_stats.csv if it exists, otherwise return defaults."""
    default_stats = {
        'height_cm': 175.0,
        'weight_kg': 70.0,
        'age': 30,
        'gender': 'male'
    }
    csv_path = Path(__file__).parent.parent / 'data' / 'user_stats.csv'
    if not csv_path.exists():
        return default_stats

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            return {
                'height_cm': float(row.get('height_cm', default_stats['height_cm'])),
                'weight_kg': float(row.get('weight_kg', default_stats['weight_kg'])),
                'age': int(row.get('age', default_stats['age'])),
                'gender': row.get('gender', default_stats['gender']).strip().lower()
            }
    except Exception:
        return default_stats


def calculate_tdee(height_cm: float, weight_kg: float, age: int, gender: str, activity_factor: float = 1.55) -> float:
    """
    Calculate TDEE using Mifflin-St. Jeor formula with running adjustments.

    Args:
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        age: Age in years
        gender: 'male' or 'female'
        activity_factor: Multiplier for activity level (default 1.55 for moderate)

    Returns:
        TDEE in kcal/day
    """
    # Mifflin-St. Jeor formula
    if gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Apply activity factor
    tdee = bmr * activity_factor

    # Running adjustments (additional burn)
    running_burn = 0
    if 'long_run' in os.environ.get('RUNNING_SCHEDULE', '').lower():
        long_run_distance = float(os.environ.get('LONG_RUN_DISTANCE', '18'))
        running_burn = long_run_distance * 83  # ~83 kcal per mile for average runner

    return round(tdee + running_burn)
