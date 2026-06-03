import json
import os
import re
from pathlib import Path
from src.tools.calculate_tdee import calculate_tdee


def load_static_data() -> dict:
    """Load static markdown data files."""
    foods_md = Path(__file__).parent.parent / 'data' / 'foods.md'
    macros_md = Path(__file__).parent.parent / 'data' / 'macros.md'
    rules_md = Path(__file__).parent.parent / 'data' / 'rules.md'

    return {
        'foods': foods_md.read_text(),
        'macros': macros_md.read_text(),
        'rules': rules_md.read_text()
    }


def load_state(state_path: str) -> dict:
    """Load and return the current state from JSON file."""
    state_file = Path(state_path)
    if not state_file.exists():
        return {
            'current_day': 'Monday',
            'plan_id': 'uuid-v4-placeholder',
            'plan': [],
            'grocery_list': [],
            'missing_macros': []
        }
    return json.loads(state_file.read_text())


def save_state(state: dict, state_path: str) -> bool:
    """Save state to JSON file."""
    state_file = Path(state_path)
    try:
        state_file.write_text(json.dumps(state, indent=2))
        return True
    except Exception:
        return False


def generate_meal_plan(state_path: str, user_query: str) -> str:
    """
    Generate a meal plan based on current state and user query.

    Args:
        state_path: Path to state.json
        user_query: User's request or updates

    Returns:
        Markdown string containing the meal plan
    """
    # Load state and static data
    state = load_state(state_path)
    static_data = load_static_data()

    # Parse user query for updates
    updates = parse_user_updates(user_query)

    # Calculate TDEE from state
    tdee = calculate_tdee_from_state(state)

    # Generate plan for current day
    day_plan = generate_day_plan(tdee, state, static_data, updates)

    # Update state with new plan and grocery list
    updated_state = update_plan_in_state(state, day_plan, updates)
    save_state(updated_state, state_path)

    # Format output
    return format_plan_markdown(day_plan, state)


def parse_user_updates(query: str) -> dict:
    """Parse user query to extract updates."""
    updates = {
        'ate_out': False,
        'extra_items': [],
        'removed_items': []
    }

    # Check for "ate out" or similar
    if re.search(r'ate\s*out|skipped|did not eat', query, re.IGNORECASE):
        updates['ate_out'] = True

    # Check for extra items
    extra_match = re.search(r'have\s+extra\s+(\w+)', query, re.IGNORECASE)
    if extra_match:
        updates['extra_items'].append(extra_match.group(1).lower())

    # Check for removed items
    removed_match = re.search(r'remove|skip|delete\s+(\w+)', query, re.IGNORECASE)
    if removed_match:
        updates['removed_items'].append(removed_match.group(1).lower())

    return updates


def calculate_tdee_from_state(state: dict) -> float:
    """Calculate TDEE from state data."""
    # Extract user stats from macros.md or state
    # This is a simplified version - in production, extract from state
    height = 175  # cm
    weight = 70   # kg
    age = 30      # years
    gender = 'male'

    return calculate_tdee(height, weight, age, gender)


def generate_day_plan(tdee: float, state: dict, static_data: dict, updates: dict) -> dict:
    """Generate meal plan for a single day."""
    # Determine caloric target
    is_pre_long_run = 'saturday' in state.get('current_day', '').lower()
    target_calories = 2700 if is_pre_long_run else 2250

    # Generate meals
    meals = []
    # Breakfast
    meals.append({
        'name': 'Oatmeal with berries',
        'calories': 300,
        'macros': {'protein': 10, 'carbs': 50, 'fat': 5}
    })
    # Lunch
    meals.append({
        'name': 'Chicken Thigh Stir-fry with Rice',
        'calories': 600,
        'macros': {'protein': 35, 'carbs': 45, 'fat': 20}
    })
    # Dinner
    meals.append({
        'name': 'Salmon with Quinoa and Vegetables',
        'calories': 700,
        'macros': {'protein': 30, 'carbs': 30, 'fat': 35}
    })
    # Snack
    meals.append({
        'name': 'Greek Yogurt with nuts',
        'calories': 200,
        'macros': {'protein': 20, 'carbs': 10, 'fat': 5}
    })

    # Calculate total calories
    total_calories = sum(m['calories'] for m in meals)

    # Adjust if needed
    if total_calories > target_calories:
        # Remove or reduce a meal
        meals.pop()  # Remove snack

    return {
        'day': state.get('current_day', 'Monday'),
        'meals': meals,
        'total_calories': total_calories
    }


def update_plan_in_state(state: dict, day_plan: dict, updates: dict) -> dict:
    """Update state with new plan and grocery list."""
    # Add day to plan
    state['plan'].append(day_plan)

    # Generate grocery list from meals
    grocery_items = []
    for meal in day_plan['meals']:
        item_name = meal['name']
        # Extract main ingredient
        if 'Chicken' in item_name:
            grocery_items.append({'item': 'Chicken Thighs', 'quantity': 1.5, 'unit': 'lbs', 'category': 'Protein'})
        elif 'Salmon' in item_name:
            grocery_items.append({'item': 'Salmon', 'quantity': 1, 'unit': 'lbs', 'category': 'Protein'})
        elif 'Oatmeal' in item_name:
            grocery_items.append({'item': 'Oatmeal', 'quantity': 2, 'unit': 'cups', 'category': 'Grain'})
        elif 'Quinoa' in item_name:
            grocery_items.append({'item': 'Quinoa', 'quantity': 1.5, 'unit': 'cups', 'category': 'Grain'})
        elif 'Rice' in item_name:
            grocery_items.append({'item': 'White Rice', 'quantity': 2, 'unit': 'cups', 'category': 'Grain'})
        elif 'Greek Yogurt' in item_name:
            grocery_items.append({'item': 'Greek Yogurt', 'quantity': 2, 'unit': 'cups', 'category': 'Dairy'})

    # Remove duplicates
    seen = set()
    unique_items = []
    for item in grocery_items:
        key = (item['item'], item['category'])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    state['grocery_list'] = unique_items

    # Handle updates
    if updates['ate_out']:
        state['plan'][-1]['meals'] = []

    return state


def format_plan_markdown(day_plan: dict, state: dict) -> str:
    """Format plan as Markdown code block."""
    lines = []
    lines.append(f"```\n"
                 f"## {day_plan['day']} Meal Plan\n"
                 f"\n"
                 f"### Meals\n"
                 f"\n"
                 f"| Meal | Calories | Protein | Carbs | Fat |\n"
                 f"|-----|---------|--------|-------|-----|\n")

    for meal in day_plan['meals']:
        macros = meal.get('macros', {})
        lines.append(f"| {meal['name']} | {meal['calories']} | {macros.get('protein', 0)}g | {macros.get('carbs', 0)}g | {macros.get('fat', 0)}g |")

    lines.append(f"\n### Total Calories: {day_plan['total_calories']}\n"
                 f"\n"
                 f"### Grocery List\n")

    for item in state['grocery_list']:
        lines.append(f"- {item['item']}: {item['quantity']} {item['unit']}")

    lines.append(f"\n```")

    return '\n'.join(lines)
