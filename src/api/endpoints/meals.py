from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from src.api.models import AddMealRequest, AddMealResponse, MealResponse, SearchCriteria
from src.tools.add_saved_meal import add_saved_meal_from_request
from src.tools.search_meals import search_meals
from src.tools.load_saved_meals import load_saved_meals

router = APIRouter(prefix="/meals", tags=["Meals"])


@router.post("/add", response_model=AddMealResponse)
async def add_meal(request: AddMealRequest):
    """
    Add a new saved meal to the recipe database.
    
    Args:
        request: AddMealRequest with meal details
    
    Returns:
        AddMealResponse with success status and newly added foods
    
    Example:
        POST /meals/add
        {
            "name": "Chicken Stir-fry",
            "ingredients": [
                {"name": "Chicken", "serving": "6 oz", "calories": 280, "protein": 38, "carbs": 0, "fat": 12},
                {"name": "Vegetables", "serving": "1 cup", "calories": 50, "protein": 2, "carbs": 10, "fat": 0},
                {"name": "Soy Sauce", "serving": "1 tbsp", "calories": 10, "protein": 1, "carbs": 1, "fat": 0}
            ],
            "macros": {"calories": 500, "protein": 30, "carbs": 20, "fat": 15},
            "instructions": ["Cook chicken", "Add vegetables", "Season with soy sauce"],
            "category": "Dinner",
            "tags": ["quick", "healthy"]
        }
    """
    try:
        meal_data = {
            'name': request.name,
            'ingredients': [ingredient.model_dump() for ingredient in request.ingredients],
            'macros': request.macros,
            'instructions': request.instructions,
            'category': request.category,
            'tags': request.tags,
            'servings': request.servings,
        }
        result = add_saved_meal_from_request(meal_data, prompt_session=False)
        return AddMealResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add meal: {str(e)}")


@router.get("/", response_model=List[MealResponse])
async def list_meals(
    category: Optional[str] = Query(None, description="Filter by meal category"),
    search: Optional[str] = Query(None, description="Search term for name/ingredients/tags")
):
    """
    List all saved meals with optional filtering.
    
    Args:
        category: Optional category filter (Breakfast/Lunch/Dinner/etc.)
        search: Optional search term
    
    Returns:
        List of MealResponse objects
    
    Example:
        GET /meals?category=Dinner
        GET /meals?search=chicken
    """
    try:
        meals = load_saved_meals(filter_category=category, search_term=search)
        return [MealResponse(**meal) for meal in meals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load meals: {str(e)}")


@router.get("/search", response_model=List[MealResponse])
async def search_meals_endpoint(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_cal: Optional[int] = Query(None, ge=0, description="Minimum calories"),
    max_cal: Optional[int] = Query(None, ge=0, description="Maximum calories"),
    min_prot: Optional[int] = Query(None, ge=0, description="Minimum protein (g)"),
    max_prot: Optional[int] = Query(None, ge=0, description="Maximum protein (g)"),
    min_carb: Optional[int] = Query(None, ge=0, description="Minimum carbs (g)"),
    max_carb: Optional[int] = Query(None, ge=0, description="Maximum carbs (g)"),
    min_fat: Optional[int] = Query(None, ge=0, description="Minimum fat (g)"),
    max_fat: Optional[int] = Query(None, ge=0, description="Maximum fat (g)"),
    ingredient: Optional[str] = Query(None, description="Filter by ingredient"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search_term: Optional[str] = Query(None, description="General search term")
):
    """
    Search meals with advanced filtering criteria.
    
    Args:
        category: Filter by meal category
        min_cal/max_cal: Calorie range
        min_prot/max_prot: Protein range
        min_carb/max_carb: Carbs range
        min_fat/max_fat: Fat range
        ingredient: Filter by ingredient presence
        tag: Filter by tag
        search_term: General search term for name/ingredients/tags
    
    Returns:
        List of MealResponse objects matching criteria
    
    Example:
        GET /meals/search?category=Dinner&min_cal=400&max_cal=600
        GET /meals/search?ingredient=chicken
    """
    try:
        criteria = {}
        if category:
            criteria['category'] = category
        if min_cal is not None:
            criteria['min_cal'] = min_cal
        if max_cal is not None:
            criteria['max_cal'] = max_cal
        if min_prot is not None:
            criteria['min_prot'] = min_prot
        if max_prot is not None:
            criteria['max_prot'] = max_prot
        if min_carb is not None:
            criteria['min_carb'] = min_carb
        if max_carb is not None:
            criteria['max_carb'] = max_carb
        if min_fat is not None:
            criteria['min_fat'] = min_fat
        if max_fat is not None:
            criteria['max_fat'] = max_fat
        if ingredient:
            criteria['ingredient'] = ingredient
        if tag:
            criteria['tag'] = tag
        if search_term:
            criteria['search_term'] = search_term
        
        meals = search_meals(criteria)
        return [MealResponse(**meal) for meal in meals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search meals: {str(e)}")
