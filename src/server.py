import sys
from fastmcp import FastMCP
from pathlib import Path
import os
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

mcp = FastMCP("Food & Nutrition Intelligence")

from src.tools.generate_plan import generate_meal_plan
from src.tools.update_state import update_state
from src.tools.calculate_tdee import calculate_tdee, get_user_stats
from src.tools.grocery_inventory import (
    add_inventory_items,
    add_unmatched_items,
    get_inventory,
    clear_inventory,
    format_inventory_for_cli,
)
from src.tools.food_processor import parse_ingredients, get_ingredient_metadata, get_food_match_candidates
from src.tools.add_saved_meal import add_new_food, prompt_for_macros, load_static_data as load_specialty_data, invalidate_caches

mcp.tool(name="generate_meal_plan", description="Generate a meal plan based on current state and user query.")(generate_meal_plan)
mcp.tool(name="update_state", description="Update state.json with generated plan and grocery list.")(update_state)

STATE_PATH = str(Path(__file__).parent / "state" / "state.json")
DATA_DIR = Path(__file__).parent / "data"

API_SERVER_URL = os.getenv("MEAL_PLANNER_API_URL", "http://localhost:8000")
API_KEY = os.getenv("MEAL_PLANNER_API_KEY")
if not API_KEY:
    raise RuntimeError("MEAL_PLANNER_API_KEY environment variable must be set")


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
        lines.append(f"| {item['item']} | {item['quantity']} | {item['unit']} | {item.get('category', 'Other')} |")
    return "\n".join(lines)


def show_help() -> str:
    return """Available commands:
  show_profile    - Display nutritional goals, TDEE, and current preferences
  generate_plan   - Generate a new 7-day meal plan
  show_groceries  - Display the consolidated grocery list
  add_groceries [natural text] - Add groceries from natural language
  show_inventory  - Display parsed grocery inventory
  clear_inventory - Clear grocery inventory
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
        print(f"Inventory items: {len(result.get('grocery_inventory', []))}")


def format_inventory_cli(inventory: list) -> str:
    if not inventory:
        return "Inventory is empty. Use `add_groceries` to add items."
    lines = ["## Grocery Inventory\n"]
    for item in inventory:
        name = item.get("standardized_item", item.get("raw_phrase", "Unknown"))
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        level = item.get("confidence_level", "unknown")
        score = item.get("confidence_score", 0.0)
        source = item.get("source", "unknown")
        lines.append(f"- {name}: {qty} {unit} | confidence={score:.2f} {level} | source={source}")
    return "\n".join(lines)


def _prompt_menu_choice(prompt: str, minimum: int, maximum: int) -> int:
    while True:
        choice = input(prompt).strip()
        if choice.isdigit():
            value = int(choice)
            if minimum <= value <= maximum:
                return value
        print(f"Please enter a number from {minimum} to {maximum}.")


def _build_specialty_item(meta: dict) -> dict:
    return {
        "raw_phrase": meta.get("raw_phrase", ""),
        "standardized_item": meta.get("standardized_item", meta.get("raw_phrase", "")),
        "quantity": meta.get("quantity", 1.0),
        "unit": meta.get("unit", "count/whole"),
        "corgis_style_query": meta.get("corgis_style_query", meta.get("standardized_item", "")),
        "confidence_score": meta.get("confidence_score", 0.0),
        "confidence_level": meta.get("confidence_level", "low"),
        "should_auto_save": False,
        "source": "specialty",
    }


def _save_specialty_ingredient(meta: dict) -> dict:
    print("no matches found. Will add this to specialty ingredients list as it's not in the corgis database. Please provide macros")
    macros_data = prompt_for_macros(True)
    specialty_data = load_specialty_data()
    add_new_food(meta.get("standardized_item", meta.get("raw_phrase", "")), specialty_data["specialty"], macros_data)
    invalidate_caches()
    return _build_specialty_item(meta)


def _review_uncertain_item(meta: dict) -> dict | None:
    current_meta = dict(meta)

    while True:
        candidates = get_food_match_candidates(
            current_meta.get("raw_phrase", ""),
            current_meta.get("standardized_item", ""),
            limit=3,
        )

        print(f"\nLow confidence in this ingredient: {current_meta.get('standardized_item', '')}. Is this what you meant?")

        if candidates:
            for idx, candidate in enumerate(candidates, start=1):
                confidence = f"{candidate.get('confidence_score', 0.0):.2f} confidence"
                print(f"  {idx}. {candidate.get('corgis_description', 'Unknown')} ({confidence})")
            reword_choice = len(candidates) + 1
            specialty_choice = len(candidates) + 2
            print(f"  {reword_choice}. Reword your grocery")
            print(f"  {specialty_choice}. Create a specialty ingredient. Please provide the macros of your ingredient")

            choice = _prompt_menu_choice(f"Select 1-{specialty_choice}: ", 1, specialty_choice)
            if choice <= len(candidates):
                chosen = dict(current_meta)
                chosen.update(candidates[choice - 1])
                chosen["should_auto_save"] = True
                return chosen

            if choice == specialty_choice:
                return _save_specialty_ingredient(current_meta)

            reworded_text = input("Reword the item: ").strip()
            if not reworded_text:
                print("No reworded item provided.")
                continue

            parsed_items = parse_ingredients(reworded_text)
            if not parsed_items:
                print("No ingredient found. Please reword it again or create a specialty ingredient.")
                continue

            current_meta = get_ingredient_metadata(parsed_items[0])
            continue

        print("No Corgis match candidates found.")
        print("  1. Reword your grocery")
        print("  2. Create a specialty ingredient. Please provide the macros of your ingredient")
        choice = _prompt_menu_choice("Select 1-2: ", 1, 2)
        if choice == 2:
            return _save_specialty_ingredient(current_meta)

        reworded_text = input("Reword the item: ").strip()
        if not reworded_text:
            print("No reworded item provided.")
            continue

        parsed_items = parse_ingredients(reworded_text)
        if not parsed_items:
            print("No ingredient found. Please reword it again or create a specialty ingredient.")
            continue

        current_meta = get_ingredient_metadata(parsed_items[0])


def add_groceries_cmd(args_text: str):
    text = args_text.strip() if args_text else ""
    if not text:
        text = input("Describe what you bought (natural language): ").strip()
    if not text:
        print("No input provided.")
        return

    ingredients = parse_ingredients(text)
    results = []
    to_save = []
    unmatched = []
    for item in ingredients:
        meta = get_ingredient_metadata(item)
        results.append(meta)
        if meta.get("should_auto_save") and meta.get("source") == "corgis":
            to_save.append(meta)
        else:
            resolved = _review_uncertain_item(meta)
            if resolved:
                if resolved.get("source") == "specialty":
                    to_save.append(resolved)
                else:
                    to_save.append(resolved)
            else:
                unmatched.append(meta)

    saved_count = 0
    if to_save:
        saved_count = len(add_inventory_items(to_save).get("added", []))

    if unmatched:
        add_unmatched_items(unmatched)

    print("\nGrocery Parsing Results:\n")
    print(f"| Raw | Standardized | Qty | Unit | Match | Confidence | Status |")
    print(f"|-----|--------------|-----|------|-------|------------|--------|")
    for meta in results:
        raw = meta.get("raw_phrase", "")
        std = meta.get("standardized_item", "")
        qty = meta.get("quantity", 0)
        unit = meta.get("unit", "")
        match = meta.get("corgis_description") or meta.get("source", "")
        confidence = f"{meta.get('confidence_score', 0.0):.2f} {meta.get('confidence_level', '')}"
        if meta.get("should_auto_save"):
            status = "auto"
        elif meta.get("source") == "specialty" or not meta.get("corgis_description"):
            status = "manual"
        else:
            status = "review"
        print(f"| {raw} | {std} | {qty} | {unit} | {match} | {confidence} | {status} |")

    print(f"\nSaved: {saved_count} | Review/Manual: {len(unmatched)}")

    answer = input("Generate a meal plan now? [y/N]: ").strip().lower()
    if answer == 'y':
        print("Generating meal plan...")
        result = generate_meal_plan(STATE_PATH, "generate new plan")
        print(result)


def show_inventory_cmd():
    print(format_inventory_cli(get_inventory()))


def clear_inventory_cmd():
    clear_inventory()
    print("Grocery inventory cleared.")


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
        elif cmd_lower == "add_groceries":
            add_groceries_cmd(" ".join(args))
        elif cmd_lower == "show_inventory":
            show_inventory_cmd()
        elif cmd_lower == "clear_inventory":
            clear_inventory_cmd()
        elif cmd_lower == "api":
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
