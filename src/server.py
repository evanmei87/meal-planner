import sys
from fastmcp import FastMCP
from pathlib import Path
import os
import httpx

# Add project root to sys.path so 'src.*' imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

mcp = FastMCP("Food & Nutrition Intelligence")

# Import tools
from src.tools.generate_plan import generate_meal_plan
from src.tools.update_state import update_state
from src.tools.calculate_tdee import calculate_tdee, get_user_stats

# Register tools for MCP mode
mcp.tool(name="generate_meal_plan", description="Generate a meal plan based on current state and user query.")(generate_meal_plan)
mcp.tool(name="update_state", description="Update state.json with generated plan and grocery list.")(update_state)

STATE_PATH = str(Path(__file__).parent / "state" / "state.json")
DATA_DIR = Path(__file__).parent / "data"

# API Configuration
API_SERVER_URL = os.getenv("MEAL_PLANNER_API_URL", "http://localhost:8000")
API_KEY = os.getenv("MEAL_PLANNER_API_KEY", "dev-key-change-in-production")


def load_profile_text() -> str:
    """Load and format user profile from data files."""
    specialty = (DATA_DIR / "specialty-ingredients.md").read_text()

    stats = get_user_stats()
    tdee = calculate_tdee(
        height_cm=stats['height_cm'],
        weight_kg=stats['weight_kg'],
        age=stats['age'],
        gender=stats['gender']
    )

    lines = [
        "## User Profile",
        "",
        f"**TDEE**: {tdee} kcal/day (estimated)",
        f"**Stats**: {stats['height_cm']}cm, {stats['weight_kg']}kg, {stats['age']}yo, {stats['gender']}",
        "",
        "### Macro Goals",
        "| Target | Value |",
        "|-------|-------|",
        f"| Calories | {tdee} kcal |",
        "| Protein | 150g |",
        "| Carbs | 250g |",
        "| Fat | 60g |",
        "",
        "### Specialty Ingredients",
        specialty,
    ]
    return "\n".join(lines)


def load_grocery_list_text() -> str:
    """Load and format grocery list from state."""
    state_path = Path(STATE_PATH)
    if not state_path.exists():
        return "No grocery list found. Generate a meal plan first."

    import json
    try:
        state = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return "Could not read state file. Generate a meal plan first."

    items = state.get("grocery_list", [])
    if not items:
        return "Grocery list is empty. Generate a meal plan first."

    lines = ["## Grocery List", "", "| Item | Quantity | Unit | Category |", "|------|----------|------|----------|"]
    for item in items:
        lines.append(f"| {item['item']} | {item['quantity']} | {item['unit']} | {item['category']} |")
    return "\n".join(lines)


def show_help() -> str:
    return """Available commands:
  show_profile    - Display nutritional goals, TDEE, and current preferences
  generate_plan   - Generate a new 7-day meal plan
  show_groceries  - Display the consolidated grocery list
  api plan generate [days] - Generate meal plan via API
  api meals list [category] - List saved meals via API
  api meals search [term] - Search meals via API
  api state get - Get current state via API
  help            - Show this help message
  exit            - Exit the program"""


# API Helper Functions
def make_api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make an HTTP request to the API server."""
    headers = {"X-API-Key": API_KEY}
    url = f"{API_SERVER_URL}{endpoint}"
    
    try:
        with httpx.Client() as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = client.put(url, headers=headers, json=data)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status {response.status_code}: {response.text}"}
    except httpx.ConnectError:
        return {"error": f"Could not connect to API server at {API_SERVER_URL}. Is it running?"}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def api_plan_generate(days: list = None):
    """Generate meal plan via API."""
    data = {"days": days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    result = make_api_request("POST", "/plan/generate", data)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Meal plan generated successfully!")
        print(f"Plan ID: {result.get('plan_id', 'N/A')}")
        print(f"Days: {len(result.get('plan', []))}")
        print(f"Grocery items: {len(result.get('grocery_list', []))}")


def api_meals_list(category: str = None):
    """List meals via API."""
    endpoint = "/meals/"
    if category:
        endpoint += f"?category={category}"
    
    result = make_api_request("GET", endpoint)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        meals = result if isinstance(result, list) else []
        print(f"Found {len(meals)} meal(s):")
        for meal in meals:
            print(f"  - {meal.get('name', 'N/A')} ({meal.get('category', 'N/A')})")


def api_meals_search(term: str = None):
    """Search meals via API."""
    endpoint = "/meals/search"
    if term:
        endpoint += f"?search_term={term}"
    
    result = make_api_request("GET", endpoint)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        meals = result if isinstance(result, list) else []
        print(f"Found {len(meals)} meal(s):")
        for meal in meals:
            print(f"  - {meal.get('name', 'N/A')}")


def api_state_get():
    """Get current state via API."""
    result = make_api_request("GET", "/state/")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Current day: {result.get('current_day', 'N/A')}")
        print(f"Plan ID: {result.get('plan_id', 'N/A')}")
        print(f"Plan days: {len(result.get('plan', []))}")
        print(f"Grocery items: {len(result.get('grocery_list', []))}")


if __name__ == "__main__":
    print("Food & Nutrition Intelligence — Meal Planner CLI")
    print("Type 'help' for available commands.")
    print()

    while True:
        try:
            cmd = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue

        # Parse command
        parts = cmd.split()
        cmd_lower = parts[0].lower()
        args = parts[1:]

        if cmd_lower == "exit":
            break
        elif cmd_lower == "help":
            print(show_help())
        elif cmd_lower == "show_profile":
            print(load_profile_text())
        elif cmd_lower == "generate_plan":
            print("Generating meal plan...")
            result = generate_meal_plan(STATE_PATH, "generate new plan")
            print(result)
        elif cmd_lower == "show_groceries":
            print(load_grocery_list_text())
        elif cmd_lower == "api":
            # Handle API commands
            if len(args) >= 2:
                api_cmd = f"{args[0]} {args[1]}"
                api_args = args[2:]
                
                if api_cmd == "plan generate":
                    api_plan_generate(api_args if api_args else None)
                elif api_cmd == "meals list":
                    category = api_args[0] if api_args else None
                    api_meals_list(category)
                elif api_cmd == "meals search":
                    term = api_args[0] if api_args else None
                    api_meals_search(term)
                elif api_cmd == "state get":
                    api_state_get()
                else:
                    print(f"Unknown API command: {api_cmd}")
                    print("Available API commands:")
                    print("  api plan generate [days]")
                    print("  api meals list [category]")
                    print("  api meals search [term]")
                    print("  api state get")
            else:
                print("API commands require at least 2 arguments (e.g., 'api plan generate')")
        else:
            print(f"Unknown command: {cmd_lower}. Type 'help' for available commands.")

        print()