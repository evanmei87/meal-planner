from src.tools.calculate_tdee import get_user_stats


def estimate_running_calories(distance_miles: float) -> int:
    """Estimate calories burned running a given distance.

    Uses ~1.668 kcal burned per kg of body weight per mile run — a
    pace-independent approximation (equivalent to the commonly cited
    ~1.036 kcal/kg/km, converted to miles), which fits the MVP's
    distance-only running fields.
    """
    weight_kg = get_user_stats()["weight_kg"]
    return round(weight_kg * distance_miles * 1.668)
