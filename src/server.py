from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("Food & Nutrition Intelligence")

# Import tools
from tools.generate_plan import generate_meal_plan
from tools.update_state import update_state
<<<<<<< Updated upstream
from tools.search_web import search_web_with_context
from tools.calculate_tdee import calculate_tdee, get_user_stats
=======
from tools.calculate_tdee import calculate_tdee
>>>>>>> Stashed changes

# Register tools for MCP mode
mcp.tool(name="generate_meal_plan", description="Generate a meal plan based on current state and user query.")(generate_meal_plan)
mcp.tool(name="update_state", description="Update state.json with generated plan and grocery list.")(update_state)

STATE_PATH = str(Path(__file__).parent / "state" / "state.json")
DATA_DIR = Path(__file__).parent / "data"


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
  help            - Show this help message
  exit            - Exit the program"""


if __name__ == "__main__":
    print("Food & Nutrition Intelligence — Meal Planner CLI")
    print("Type 'help' for available commands.")
    print()

    while True:
        try:
            cmd = input(">>> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue

        if cmd == "exit":
            break
        elif cmd == "help":
            print(show_help())
        elif cmd == "show_profile":
            print(load_profile_text())
        elif cmd == "generate_plan":
            print("Generating meal plan...")
            result = generate_meal_plan(STATE_PATH, "generate new plan")
            print(result)
        elif cmd == "show_groceries":
            print(load_grocery_list_text())
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")

        print()