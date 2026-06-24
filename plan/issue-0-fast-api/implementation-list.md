# Implementation Checklist: FastAPI Migration

> **Actor Instructions**: 
> 1. Claim a step
> 2. Execute the task. 
> 3. Run the exact Verification command provided.
> 4. Mark the checkbox `[x]` ONLY upon successful verification.
> 5. If a blocker occurs, immediately stop and generate a `handoff-{step-number}.md` detailing the state, the roadblock, and current code delta. Do not proceed to the next step.

- [x] **Step 1: Update Dependencies and Setup**
  - **Context Files**: `requirements.txt`, `pyproject.toml`
  - **Objective**: Add FastAPI, Uvicorn, Pydantic, and httpx to requirements. Update project configuration.
  - **Implementation Details**: 
    - Edit `requirements.txt` to add: `fastapi>=0.104.1`, `uvicorn[standard]>=0.24.0`, `pydantic>=2.5.0`, `python-multipart>=0.0.6`, `httpx>=0.25.0`
    - Ensure Python 3.12+ requirement is properly set in `pyproject.toml`
    - Test that all dependencies install without conflicts
  - **Explicit Dependencies**: None
  - **Verification/Test Criteria**: `uv pip install -r requirements.txt` should succeed without conflicts, `import fastapi` should work in Python

- [x] **Step 2: Create API Directory Structure**
  - **Context Files**: Create `src/api/` directory with `__init__.py`, `main.py`, `models.py`, and `endpoints/` subdirectory
  - **Objective**: Set up the basic FastAPI application structure with proper package organization
  - **Implementation Details**: 
    - Create directory: `mkdir -p src/api/endpoints`
    - Create `src/api/__init__.py` with empty content
    - Create `src/api/main.py` with basic FastAPI app setup
    - Create `src/api/models.py` with initial Pydantic imports
    - Create `src/api/endpoints/__init__.py` with empty content
  - **Explicit Dependencies**: Must be completed after Step 1
  - **Verification/Test Criteria**: Directory structure should exist and be importable: `python -c "from src.api.main import app; print('FastAPI app imported successfully')"`

- [x] **Step 3: Implement Pydantic Models**
  - **Context Files**: `src/api/models.py`
  - **Objective**: Create Pydantic models for all API request/response schemas based on existing tool function signatures
  - **Implementation Details**: 
    - Import necessary Pydantic components: `BaseModel`, `Field`, `List`, `Optional`, `Literal`
    - Create `MealPlanRequest` model with `days` list and `preferences` optional string
    - Create `TDEERequest` model with `height_cm`, `weight_kg`, `age`, `gender` fields
    - Create `MealPlanResponse` model matching existing plan structure
    - Create `GroceryItem` model for grocery list items
    - Create `DayPlan` model for daily meal plans
    - Create `MealItem` model for individual meals
    - Create `StateResponse` model for state endpoint
    - Create `ErrorResponse` model for error responses
  - **Explicit Dependencies**: Must be completed after Step 2
  - **Verification/Test Criteria**: Models should validate correctly and match existing data structures: `python -c "from src.api.models import MealPlanRequest; req = MealPlanRequest(); print('Model validation works')"`

- [x] **Step 4: Refactor Tools for JSON Input**
  - **Context Files**: `src/tools/*.py`
  - **Objective**: Modify all tool functions to accept JSON parameters instead of CLI args, maintaining existing functionality
  - **Implementation Details**: 
    - **`tools/generate_plan.py`**: 
      - Modify `generate_meal_plan()` to accept `state_path` and `request_data` dict instead of CLI args
      - Update `parse_user_updates()` to work with structured data instead of string parsing
      - Ensure all existing functionality is preserved
    - **`tools/update_state.py`**: 
      - Modify `update_state()` to accept structured plan data instead of CLI arguments
      - Add validation for required fields
    - **`tools/add_saved_meal.py`**: 
      - Modify `add_saved_meal()` to accept meal data as dict instead of individual parameters
      - Update validation functions to work with structured data
    - **`tools/search_meals.py`**: 
      - Modify `search_meals()` to accept filter parameters as dict instead of individual args
      - Update `load_saved_meals()` to work with structured filter parameters
    - **`tools/load_saved_meals.py`**: 
      - Ensure compatibility with new structured input format
    - **`tools/calculate_tdee.py`**: 
      - Keep `calculate_tdee()` and `get_user_stats()` unchanged (no API endpoints for TDEE)
  - **Explicit Dependencies**: Must be completed after Step 3
  - **Verification/Test Criteria**: Existing unit tests should still pass: `pytest tests/test_*.py -v`, tools should work with JSON input: `python -c "from tools.generate_plan import generate_meal_plan; print('Tools work with JSON')"`

- [x] **Step 5: Implement Meal Plan Endpoints**
  - **Context Files**: `src/api/endpoints/meal_plan.py`, `src/api/main.py`
  - **Objective**: Create `/plan/generate`, `/plan/{day}`, and `/plan` endpoints with proper authentication and error handling
  - **Implementation Details**: 
    - Create `src/api/endpoints/meal_plan.py` with:
      - `POST /plan/generate` - calls `generate_meal_plan()` with validated request
      - `GET /plan/{day}` - returns meal plan for specific day from state
      - `GET /plan` - returns current complete plan
    - Handle authentication using middleware from Step 9
    - Implement proper error handling with HTTP status codes
    - Return structured JSON responses matching Pydantic models
    - Include request/response examples in docstrings
  - **Explicit Dependencies**: Must be completed after Step 4
  - **Verification/Test Criteria**: Endpoints should be accessible via HTTP and return correct JSON responses: `curl -X POST http://localhost:8000/plan/generate -H "Content-Type: application/json" -H "X-API-Key: dev-key" -d '{"days": ["Monday"]}'`

- [x] **Step 6: Implement Meals Endpoints**
  - **Context Files**: `src/api/endpoints/meals.py`, `src/api/main.py`
  - **Objective**: Create `/meals/add`, `/meals`, and `/meals/search` endpoints
  - **Implementation Details**: 
    - Create `src/api/endpoints/meals.py` with:
      - `POST /meals/add` - calls `add_saved_meal()` with meal data
      - `GET /meals` - returns list of all saved meals with optional category filter
      - `GET /meals/search` - returns meals matching search criteria
    - Implement proper request validation using Pydantic models
    - Handle authentication via middleware
    - Include pagination and filtering parameters
    - Return structured JSON responses with meal data
  - **Explicit Dependencies**: Must be completed after Step 5
  - **Verification/Test Criteria**: Endpoints should handle meal operations correctly: `curl -X GET http://localhost:8000/meals?category=Dinner -H "X-API-Key: dev-key"`

- [x] **Step 7: Implement State Endpoints**
  - **Context Files**: `src/api/endpoints/state.py`, `src/api/main.py`
  - **Objective**: Create `/state` GET and PUT endpoints
  - **Implementation Details**: 
    - Create `src/api/endpoints/state.py` with:
      - `GET /state` - returns current state from `state.json`
      - `PUT /state` - updates state with new plan data
    - Use existing `update_state()` function for PUT operations
    - Implement proper validation for state data structure
    - Handle authentication via middleware
    - Return structured JSON responses matching state schema
  - **Explicit Dependencies**: Must be completed after Step 6
  - **Verification/Test Criteria**: State should be readable and updatable via API: `curl -X GET http://localhost:8000/state -H "X-API-Key: dev-key"`

- [x] **Step 8: Add Authentication Middleware**
  - **Context Files**: `src/api/main.py`
  - **Objective**: Implement API key authentication middleware
  - **Implementation Details**: 
    - Create dependency function `get_api_key()` that extracts key from `X-API-Key` header
    - Add environment variable support for `MEAL_PLANNER_API_KEY`
    - Set default development key: `dev-key-change-in-production`
    - Add middleware to check API key before processing requests
    - Include proper error responses for missing/invalid keys
    - Add API key to FastAPI dependencies
  - **Explicit Dependencies**: Must be completed after Step 7
  - **Verification/Test Criteria**: Endpoints should require valid API key: `curl -X GET http://localhost:8000/plan -H "X-API-Key: invalid"` should return 401

- [x] **Step 9: Create API Tests**
  - **Context Files**: `tests/test_api/` directory with individual test files
  - **Objective**: Write comprehensive tests for all API endpoints using pytest and httpx
  - **Implementation Details**: 
    - Create `tests/test_api/conftest.py` with test fixtures and mock setup
    - Create `tests/test_api/test_meal_plan.py` with tests for meal plan endpoints:
      - Test successful meal plan generation
      - Test invalid request data
      - Test missing API key
      - Test different day combinations
      - Test response structure validation
    - Create `tests/test_api/test_meals.py` with tests for meals endpoints:
      - Test meal listing with filters
      - Test meal search functionality
      - Test meal addition with validation
      - Test error scenarios
    - Create `tests/test_api/test_state.py` with tests for state endpoints:
      - Test state retrieval
      - Test state updates
      - Test validation errors
    - Use mocking to isolate API tests from existing tool tests
    - Test both success and error scenarios
    - Ensure tests don't overlap with existing unit tests
  - **Explicit Dependencies**: Must be completed after Step 8
  - **Verification/Test Criteria**: All tests should pass: `pytest tests/test_api/ -v`, tests should cover request/response structure validation

- [x] **Step 10: Update CLI to Call API**
  - **Context Files**: `src/server.py`
  - **Objective**: Add CLI command to call API endpoints for testing and demonstration
  - **Implementation Details**: 
    - Add new CLI command: `api` that can call various endpoints
    - Implement HTTP client using `httpx` to make requests to local FastAPI server
    - Add commands like:
      - `api plan generate` - calls plan generation endpoint
      - `api meals list` - lists saved meals
      - `api state get` - gets current state
    - Include proper error handling and response formatting
    - Add configuration for API server URL and API key
    - Ensure CLI remains functional alongside API
  - **Explicit Dependencies**: Must be completed after Step 9
  - **Verification/Test Criteria**: CLI should be able to call API endpoints successfully: `python src/server.py api plan generate`

- [ ] **Step 11: Update Documentation**
  - **Context Files**: `README.md`
  - **Objective**: Add API documentation, Swagger UI instructions, and usage examples
  - **Implementation Details**: 
    - Add API overview section explaining endpoints and authentication
    - Include Swagger UI access instructions: `uv run src/api/main.py` then visit `http://localhost:8000/docs`
    - Add curl examples for all endpoints
    - Include request/response format documentation
    - Add API key setup instructions
    - Document error response formats
    - Include troubleshooting section
  - **Explicit Dependencies**: Must be completed after Step 10
  - **Verification/Test Criteria**: Documentation should be complete and accurate: `uv run src/api/main.py` and verify Swagger UI loads correctly

- [ ] **Step 12: Integration Testing**
  - **Context Files**: All API components, existing tests
  - **Objective**: Run full integration test suite to ensure both CLI and API work together
  - **Implementation Details**: 
    - Run all existing tests to ensure no regression: `pytest tests/`
    - Run all new API tests: `pytest tests/test_api/`
    - Test CLI and API interoperability
    - Test state persistence between CLI and API calls
    - Test error handling across both interfaces
    - Verify that existing functionality is preserved
  - **Explicit Dependencies**: Must be completed after Step 11
  - **Verification/Test Criteria**: All tests pass, both CLI and API functional: `pytest tests/ -v && pytest tests/test_api/ -v`