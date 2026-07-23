from typing import Optional

from src.tools.calculate_tdee import get_user_stats

MET_BY_TYPE = {"walking": 3.5, "biking": 7.5, "swimming": 6.0, "strength": 5.0}


def estimate_running_calories(distance_miles: float) -> int:
    """Estimate calories burned running a given distance.

    Uses ~1.668 kcal burned per kg of body weight per mile run — a
    pace-independent approximation (equivalent to the commonly cited
    ~1.036 kcal/kg/km, converted to miles), which fits the MVP's
    distance-only running fields.
    """
    weight_kg = get_user_stats()["weight_kg"]
    return round(weight_kg * distance_miles * 1.668)


def estimate_calories(exercise_type: str, distance_miles: Optional[float], duration_minutes: float) -> int:
    """Estimate calories burned for any supported exercise type.

    Running keeps its distance-based estimate; every other type uses a
    standard MET formula (MET * weight_kg * hours) with a fixed MET value
    per type.
    """
    if exercise_type == "running":
        return estimate_running_calories(distance_miles)

    weight_kg = get_user_stats()["weight_kg"]
    met = MET_BY_TYPE[exercise_type]
    return round(met * weight_kg * (duration_minutes / 60))
