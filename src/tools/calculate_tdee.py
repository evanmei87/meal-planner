import json
import os


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
