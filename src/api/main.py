import os
import sys
from pathlib import Path

# Add project root to sys.path so 'src.*' imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.api.endpoints import meal_plan, meals, state, groceries, exercises, exercise_presets

app = FastAPI(
    title="Meal Planner API",
    description="AI-driven meal planning assistant with MCP integration",
    version="0.1.0"
)

# API Key Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

API_KEY = os.getenv("MEAL_PLANNER_API_KEY")
if not API_KEY:
    raise RuntimeError("MEAL_PLANNER_API_KEY environment variable must be set")


async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate API key from X-API-Key header.
    
    Args:
        api_key_header: API key from request header
    
    Returns:
        The validated API key
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if api_key_header == API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


# Include routers with authentication dependency
app.include_router(meal_plan.router, dependencies=[Security(get_api_key)])
app.include_router(meals.router, dependencies=[Security(get_api_key)])
app.include_router(state.router, dependencies=[Security(get_api_key)])
app.include_router(groceries.router, dependencies=[Security(get_api_key)])
app.include_router(exercises.router, dependencies=[Security(get_api_key)])
app.include_router(exercise_presets.router, dependencies=[Security(get_api_key)])


@app.get("/")
async def root():
    return {"message": "Meal Planner API"}
