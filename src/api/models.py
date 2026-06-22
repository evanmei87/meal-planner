from pydantic import BaseModel, Field
from typing import List, Optional, Literal


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


class UpdateStateRequest(BaseModel):
    """Request to update state."""
    plan: Optional[List[DayPlan]] = None
    grocery_list: Optional[List[GroceryItem]] = None
    missing_macros: Optional[List[str]] = None
    current_day: Optional[str] = None
    grocery_inventory: Optional[List[dict]] = None
    unmatched_groceries: Optional[List[dict]] = None
    inventory_usage: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None
