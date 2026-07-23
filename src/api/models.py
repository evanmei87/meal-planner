from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal

ExerciseType = Literal["running", "walking", "biking", "swimming", "strength"]


def _require_fields_for_exercise_type(
    exercise_type: str, distance_miles: Optional[float], sets: Optional[int], reps: Optional[int]
) -> None:
    """Raise ValueError if the fields required for the given exercise type are missing.

    distance_miles is required for running/walking/biking/swimming; sets and
    reps are required for strength.
    """
    if exercise_type == "strength":
        if sets is None or reps is None:
            raise ValueError("sets and reps are required for strength exercises")
    elif distance_miles is None:
        raise ValueError("distance_miles is required for running, walking, biking, and swimming exercises")


class MealItem(BaseModel):
    """Individual meal with nutritional information."""
    name: str
    calories: int
    macros: dict = Field(default_factory=lambda: {"protein": 0, "carbs": 0, "fat": 0})
    ingredients: List[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    """Meal plan for a single day."""
    day: str
    meals: List[MealItem] = Field(default_factory=list)
    total_calories: int = 0
    total_protein: int = 0
    total_carbs: int = 0


class GroceryItem(BaseModel):
    """Item in the grocery list."""
    item: str
    quantity: float
    unit: str
    category: str


class MealPlanRequest(BaseModel):
    """Request to generate a meal plan."""
    days: List[str] = Field(
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        description="Days to generate meal plans for"
    )
    preferences: Optional[str] = Field(None, description="User preferences or updates")


class MealPlanResponse(BaseModel):
    """Response containing the generated meal plan."""
    plan_id: str
    plan: List[DayPlan] = Field(default_factory=list)
    grocery_list: List[GroceryItem] = Field(default_factory=list)
    status: str = "success"
    message: Optional[str] = None


class TDEERequest(BaseModel):
    """Request to calculate TDEE."""
    height_cm: float = Field(..., gt=0, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    age: int = Field(..., gt=0, description="Age in years")
    gender: Literal["male", "female"] = Field(..., description="Gender")
    activity_factor: float = Field(default=1.55, gt=0, description="Activity level multiplier")


class TDEEResponse(BaseModel):
    """Response with calculated TDEE."""
    tdee: float
    bmr: float
    activity_factor: float


class AddMealRequest(BaseModel):
    """Request to add a saved meal."""
    name: str = Field(..., min_length=1, description="Meal name")
    ingredients: List[str] = Field(..., min_length=1, description="List of ingredients")
    macros: dict = Field(..., description="Macros with keys: calories, protein, carbs, fat")
    instructions: List[str] = Field(..., min_length=1, description="Cooking instructions")
    category: str = Field(default="Dinner", description="Meal category")
    servings: int = Field(default=1, ge=1, description="Number of servings the recipe yields")
    tags: List[str] = Field(default_factory=list, description="Meal tags")


class AddMealResponse(BaseModel):
    """Response after adding a meal."""
    success: bool
    meal_name: str
    newly_added: List[str] = Field(default_factory=list)
    category: str
    message: str


class MealResponse(BaseModel):
    """Response with meal details."""
    name: str
    version: str
    category: str
    servings: int = Field(default=1, ge=1)
    macros: dict
    ingredients: List[str]
    instructions: List[str]
    tags: List[str]


class SearchCriteria(BaseModel):
    """Criteria for searching meals."""
    category: Optional[str] = None
    min_cal: Optional[int] = Field(None, ge=0)
    max_cal: Optional[int] = Field(None, ge=0)
    min_prot: Optional[int] = Field(None, ge=0)
    max_prot: Optional[int] = Field(None, ge=0)
    min_carb: Optional[int] = Field(None, ge=0)
    max_carb: Optional[int] = Field(None, ge=0)
    min_fat: Optional[int] = Field(None, ge=0)
    max_fat: Optional[int] = Field(None, ge=0)
    ingredient: Optional[str] = None
    tag: Optional[str] = None
    search_term: Optional[str] = None


class StateResponse(BaseModel):
    """Response with current state."""
    current_day: str
    plan_id: str
    plan: List[DayPlan] = Field(default_factory=list)
    grocery_list: List[GroceryItem] = Field(default_factory=list)
    missing_macros: List[str] = Field(default_factory=list)
    grocery_inventory: List[dict] = Field(default_factory=list)
    unmatched_groceries: List[dict] = Field(default_factory=list)
    inventory_usage: dict = Field(default_factory=lambda: {"used": [], "unused": [], "supplemental": []})
    preferences: Optional[str] = None
    normalized_exclusions: Optional[List[str]] = None


class UpdateStateRequest(BaseModel):
    """Request to update state."""
    plan: Optional[List[DayPlan]] = None
    grocery_list: Optional[List[GroceryItem]] = None
    missing_macros: Optional[List[str]] = None
    current_day: Optional[str] = None
    grocery_inventory: Optional[List[dict]] = None
    unmatched_groceries: Optional[List[dict]] = None
    inventory_usage: Optional[dict] = None
    preferences: Optional[str] = None
    normalized_exclusions: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None


class ExerciseItem(BaseModel):
    """Individual exercise entry."""
    id: str
    type: ExerciseType = "running"
    distance_miles: Optional[float] = Field(None, gt=0)
    duration_minutes: float = Field(..., gt=0)
    sets: Optional[int] = Field(None, gt=0)
    reps: Optional[int] = Field(None, gt=0)
    calories: int = 0
    notes: Optional[str] = None
    order: int = 0

    @model_validator(mode="after")
    def _check_required_fields_for_type(self) -> "ExerciseItem":
        _require_fields_for_exercise_type(self.type, self.distance_miles, self.sets, self.reps)
        return self


class ExerciseDayPlan(BaseModel):
    """Scheduled exercises for a single calendar date."""
    date: str
    day_name: str
    exercises: List[ExerciseItem] = Field(default_factory=list)
    total_calories: int = 0


class ExerciseWeekResponse(BaseModel):
    """A week of exercise days, keyed by real calendar dates."""
    week_start: str
    days: List[ExerciseDayPlan] = Field(default_factory=list)


class ExerciseMonthResponse(BaseModel):
    """A full calendar month of exercise days, keyed by real calendar dates."""
    month: str
    days: List[ExerciseDayPlan] = Field(default_factory=list)


class AddExerciseRequest(BaseModel):
    """Request to add an exercise to a given date."""
    date: str
    type: ExerciseType = "running"
    distance_miles: Optional[float] = Field(None, gt=0)
    duration_minutes: float = Field(..., gt=0)
    sets: Optional[int] = Field(None, gt=0)
    reps: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_required_fields_for_type(self) -> "AddExerciseRequest":
        _require_fields_for_exercise_type(self.type, self.distance_miles, self.sets, self.reps)
        return self


class UpdateExerciseRequest(BaseModel):
    """Request to update an existing exercise, optionally moving it to a
    different day.

    type has no default and is optional, so omitting it preserves the
    exercise's existing stored type rather than resetting it to "running".
    The endpoint resolves the effective type (request.type if provided,
    else the stored value) and validates the merged result against it,
    since only the endpoint knows the stored type.

    date is optional; when present, the endpoint moves the exercise to
    that day instead of leaving it on its existing one. order is optional
    and, when present, persists this exercise's position within its day
    (see PUT /exercises/reorder for reordering a whole day at once).
    """
    type: Optional[ExerciseType] = None
    distance_miles: Optional[float] = Field(None, gt=0)
    duration_minutes: float = Field(..., gt=0)
    sets: Optional[int] = Field(None, gt=0)
    reps: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None
    date: Optional[str] = None
    order: Optional[int] = None

    @model_validator(mode="after")
    def _check_required_fields_for_type(self) -> "UpdateExerciseRequest":
        if self.type is not None:
            _require_fields_for_exercise_type(self.type, self.distance_miles, self.sets, self.reps)
        return self


class ReorderExercisesRequest(BaseModel):
    """Request to persist a new within-day ordering for exercises."""
    date: str
    ordered_ids: List[str]


class PresetExerciseItem(BaseModel):
    """A single exercise within a day-of-week preset (no id/date/calories —
    presets are a reusable template, not a scheduled instance)."""
    type: ExerciseType = "running"
    distance_miles: Optional[float] = Field(None, gt=0)
    duration_minutes: float = Field(..., gt=0)
    sets: Optional[int] = Field(None, gt=0)
    reps: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_required_fields_for_type(self) -> "PresetExerciseItem":
        _require_fields_for_exercise_type(self.type, self.distance_miles, self.sets, self.reps)
        return self


class ExercisePresetsResponse(BaseModel):
    """Full presets map, keyed by day-of-week name."""
    presets: dict[str, List[PresetExerciseItem]] = Field(default_factory=dict)


class GroceriesRequest(BaseModel):
    """Request to parse natural-language grocery text."""
    text: str = Field(..., min_length=1, description="Natural language grocery description")


class GroceryParseResult(BaseModel):
    """Single parsed grocery item row."""
    raw_phrase: str
    standardized_item: str
    quantity: float
    unit: str
    match: str
    confidence_score: float
    confidence_level: str
    status: str  # "auto" | "review" | "manual"


class GroceriesResponse(BaseModel):
    """Response after parsing and saving grocery text."""
    items: List[GroceryParseResult]
    saved_count: int
    review_count: int
