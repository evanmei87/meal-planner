import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from src.tools.calculate_tdee import calculate_tdee, get_user_stats
from src.tools.grocery_inventory import get_inventory, is_perishable, record_inventory_usage
from src.tools.load_saved_meals import load_saved_meals


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_static_data() -> dict:
    """Load static data files: standardized food.csv plus specialty and rules."""
    data_dir = Path(__file__).parent.parent / 'data'
    food_csv = data_dir / 'food.csv'
    specialty_md = data_dir / 'specialty-ingredients.md'
    rules_md = data_dir / 'rules.md'

    return {
        'food_db': food_csv.read_text(),
        'specialty': specialty_md.read_text(),
        'rules': rules_md.read_text()
    }


def load_state(state_path: str) -> dict:
    """Load and return the current state from JSON file."""
    state_file = Path(state_path)
    if not state_file.exists():
        return _default_state()

    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return _default_state()


def _default_state() -> dict:
    return {
        'current_day': 'Monday',
        'plan_id': 'uuid-v4-placeholder',
        'plan': [],
        'grocery_list': [],
        'missing_macros': [],
        'grocery_inventory': [],
        'unmatched_groceries': [],
        'inventory_usage': {'used': [], 'unused': [], 'supplemental': []}
    }


def save_state(state: dict, state_path: str) -> bool:
    """Save state to JSON file."""
    state_file = Path(state_path)
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2))
        return True
    except Exception:
        return False


def get_current_day_est() -> str:
    """Return the current day name in EST/EDT timezone."""
    est = timezone(timedelta(hours=-4))
    now = datetime.now(est)
    return now.strftime('%A')


def get_days_to_generate(current_day: str) -> list[str]:
    """Return days from current_day through Sunday."""
    if current_day not in DAYS:
        return DAYS

    idx = DAYS.index(current_day)
    return DAYS[idx:]


def get_next_day(day: str) -> str:
    """Return the day after the given day."""
    idx = DAYS.index(day)
    next_idx = (idx + 1) % len(DAYS)
    return DAYS[next_idx]


def generate_meal_plan(state_path: str, user_query: str) -> str:
    """
    Generate a meal plan based on current state and user query.
    When inventory exists, prioritize meals that use inventory items and
    produce a supplemental grocery list for missing ingredients.
    """
    state = load_state(state_path)
    static_data = load_static_data()
    updates = parse_user_updates(user_query)
    tdee = calculate_tdee_from_state(state)

    current_day = get_current_day_est()
    state['current_day'] = current_day
    days_to_generate = get_days_to_generate(current_day)

    inventory = get_inventory()

    candidate_meals = _build_candidate_meals(state, inventory)

    day_plans = []
    for day_name in days_to_generate:
        day_plan = generate_day_plan(tdee, day_name, state, static_data, updates, candidates=candidate_meals)
        day_plans.append(day_plan)

    updated_state = update_plan_in_state(state, day_plans, days_to_generate, updates, inventory=inventory)
    save_state(updated_state, state_path)

    return format_plan_markdown(day_plans, updated_state)


def generate_meal_plan_from_request(state_path: str, request_data: dict) -> dict:
    """
    Generate a meal plan from structured request data (for API use).

    Args:
        state_path: Path to state.json
        request_data: Dictionary with keys:
            - days: List of day names to generate
            - preferences: Optional string with user preferences

    Returns:
        Dictionary with generated plan data
    """
    state = load_state(state_path)
    static_data = load_static_data()

    # Parse updates from preferences if provided
    preferences = request_data.get('preferences', '')
    updates = parse_user_updates(preferences) if preferences else {
        'ate_out': False,
        'extra_items': [],
        'removed_items': []
    }

    tdee = calculate_tdee_from_state(state)

    # Use requested days or default to current day through Sunday
    requested_days = request_data.get('days', [])
    if requested_days:
        days_to_generate = requested_days
    else:
        current_day = get_current_day_est()
        state['current_day'] = current_day
        days_to_generate = get_days_to_generate(current_day)

    inventory = get_inventory()
    candidate_meals = _build_candidate_meals(state, inventory)

    day_plans = []
    for day_name in days_to_generate:
        day_plan = generate_day_plan(tdee, day_name, state, static_data, updates, candidates=candidate_meals)
        day_plans.append(day_plan)

    updated_state = update_plan_in_state(state, day_plans, days_to_generate, updates, inventory=inventory)
    save_state(updated_state, state_path)

    return {
        'plan_id': state.get('plan_id', 'unknown'),
        'plan': day_plans,
        'grocery_list': updated_state.get('grocery_list', []),
        'status': 'success'
    }


def parse_user_updates(query: str) -> dict:
    """Parse user query to extract updates."""
    updates = {
        'ate_out': False,
        'extra_items': [],
        'removed_items': []
    }

    if re.search(r'ate\s*out|skipped|did not eat', query, re.IGNORECASE):
        updates['ate_out'] = True

    extra_match = re.search(r'have\s+extra\s+(\w+)', query, re.IGNORECASE)
    if extra_match:
        updates['extra_items'].append(extra_match.group(1).lower())

    removed_match = re.search(r'(?:remove|skip|delete)\s+(\w+)', query, re.IGNORECASE)
    if removed_match:
        updates['removed_items'].append(removed_match.group(1).lower())

    return updates


def calculate_tdee_from_state(state: dict) -> float:
    """Calculate TDEE from state data."""
    stats = get_user_stats()
    return calculate_tdee(stats['height_cm'], stats['weight_kg'], stats['age'], stats['gender'])


# Grains strictly limited to: White Rice, Quinoa, Oatmeal (per meal-plan-requirements.md)
# Protein types: max 3 distinct large protein types per week (eggs excluded)
#   Chosen: Chicken Thighs, Chicken Breast, Salmon
# Vegetables: max 5 distinct types per week
#   Chosen: Mushrooms, Spinach, Bell Peppers, Green Beans, Broccoli

PROTEIN_SHAKE = {
    'name': 'Protein Shake (2 scoops)',
    'calories': 250,
    'macros': {'protein': 32, 'carbs': 8, 'fat': 5},
    'ingredients': ['Protein Powder', 'Almond Milk'],
}

BREAKFAST_OPTIONS = [
    {'name': 'Oatmeal with Berries', 'calories': 500, 'macros': {'protein': 25, 'carbs': 70, 'fat': 12}, 'ingredients': ['Oatmeal', 'Mixed Berries', 'Milk']},
    {'name': 'Oatmeal with Greek Yogurt', 'calories': 520, 'macros': {'protein': 30, 'carbs': 65, 'fat': 10}, 'ingredients': ['Oatmeal', 'Greek Yogurt', 'Honey']},
    {'name': 'Oatmeal with Scrambled Eggs', 'calories': 500, 'macros': {'protein': 28, 'carbs': 60, 'fat': 16}, 'ingredients': ['Oatmeal', 'Eggs', 'Butter']},
    {'name': 'Oatmeal and Protein Shake', 'calories': 530, 'macros': {'protein': 38, 'carbs': 65, 'fat': 10}, 'ingredients': ['Oatmeal', 'Protein Powder', 'Banana', 'Almond Milk']},
]

LUNCH_OPTIONS = [
    {'name': 'Chicken Thigh Stir-fry with Rice', 'calories': 750, 'macros': {'protein': 48, 'carbs': 60, 'fat': 25}, 'ingredients': ['Chicken Thighs', 'White Rice', 'Mushrooms', 'Soy Sauce']},
    {'name': 'Salmon Rice Bowl', 'calories': 720, 'macros': {'protein': 40, 'carbs': 55, 'fat': 28}, 'ingredients': ['Salmon', 'White Rice', 'Spinach', 'Soy Sauce']},
    {'name': 'Grilled Chicken Rice Plate', 'calories': 700, 'macros': {'protein': 50, 'carbs': 60, 'fat': 20}, 'ingredients': ['Chicken Breast', 'White Rice', 'Green Beans', 'Olive Oil']},
]

DINNER_OPTIONS = [
    {'name': 'Salmon Quinoa Bowl', 'calories': 750, 'macros': {'protein': 50, 'carbs': 40, 'fat': 28}, 'ingredients': ['Salmon', 'Quinoa', 'Broccoli', 'Olive Oil']},
    {'name': 'Chicken Breast with Quinoa', 'calories': 730, 'macros': {'protein': 50, 'carbs': 38, 'fat': 28}, 'ingredients': ['Chicken Breast', 'Quinoa', 'Green Beans', 'Olive Oil']},
    {'name': 'Salmon with Quinoa and Spinach', 'calories': 760, 'macros': {'protein': 45, 'carbs': 45, 'fat': 32}, 'ingredients': ['Salmon', 'Quinoa', 'Spinach', 'Olive Oil']},
]

EXTRA_SNACK_OPTIONS = [
    {'name': 'Greek Yogurt with Nuts', 'calories': 280, 'macros': {'protein': 25, 'carbs': 15, 'fat': 12}, 'ingredients': ['Greek Yogurt', 'Mixed Nuts']},
    {'name': 'Cottage Cheese', 'calories': 240, 'macros': {'protein': 28, 'carbs': 10, 'fat': 5}, 'ingredients': ['Cottage Cheese']},
    {'name': 'Hard-boiled Eggs', 'calories': 280, 'macros': {'protein': 24, 'carbs': 5, 'fat': 18}, 'ingredients': ['Eggs']},
]

_CORE_SLOTS = [BREAKFAST_OPTIONS, LUNCH_OPTIONS, DINNER_OPTIONS]


def _inventory_lookup_key(name: str) -> str:
    return name.lower().strip()


def _excluded_terms(preferences: str) -> list[str]:
    """Extract excluded ingredient/meal terms from a preferences string.

    Parses comma-separated phrases of the form "no X" and returns [X, ...].
    Other phrases (e.g. "high protein") are ignored.
    """
    excluded = []
    for phrase in preferences.lower().split(','):
        phrase = phrase.strip()
        if phrase.startswith('no '):
            excluded.append(phrase[3:].strip())
    return excluded


def _meal_allowed(meal: dict, excluded: list[str]) -> bool:
    """Return True if no excluded term appears in the meal name or ingredients."""
    if not excluded:
        return True
    meal_text = (meal.get('name', '') + ' ' + ' '.join(meal.get('ingredients', []))).lower()
    return not any(term.lower() in meal_text for term in excluded)


def _build_candidate_meals(state: dict, inventory: list[dict]) -> list[dict]:
    hardcoded = []
    for slot in _CORE_SLOTS:
        hardcoded.extend(slot)
    hardcoded.append(PROTEIN_SHAKE)
    hardcoded.extend(EXTRA_SNACK_OPTIONS)

    saved = load_saved_meals()
    combined = list(hardcoded)
    for meal in saved:
        if meal.get("category", "").lower() in {"breakfast", "lunch", "dinner", "snack"}:
            combined.append({
                "name": meal["name"],
                "calories": meal["macros"].get("calories", 0),
                "macros": meal["macros"],
                "ingredients": meal.get("ingredients", []),
                "category": meal.get("category", ""),
            })

    preferences = state.get('preferences', '') or ''
    excluded = _excluded_terms(preferences)
    combined = [m for m in combined if _meal_allowed(m, excluded)]

    inventory_names = {_inventory_lookup_key(i.get("standardized_item", i.get("raw_phrase", ""))) for i in inventory}

    scored = []
    for meal in combined:
        ingredients = [i for i in meal.get("ingredients", [])]
        matched = sum(1 for ing in ingredients if _inventory_lookup_key(ing) in inventory_names)
        perishable_matched = sum(2 for ing in ingredients if is_perishable({"standardized_item": ing, "raw_phrase": ing}) and _inventory_lookup_key(ing) in inventory_names)
        score = matched + perishable_matched
        scored.append((score, meal))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _pick_meal(slot_options: list[dict], day_index: int) -> dict:
    """Pick a meal from slot_options cycling by day_index so each day varies."""
    return slot_options[day_index % len(slot_options)]


def generate_day_plan(tdee: float, day_name: str, state: dict, static_data: dict, updates: dict, candidates: list[dict] | None = None) -> dict:
    """Generate meal plan for a single day, compliant with meal-plan-requirements.md."""
    is_pre_long_run = 'friday' in day_name.lower()
    target_calories = 2700 if is_pre_long_run else 2250

    day_index = DAYS.index(day_name)

    if candidates:
        inventory = get_inventory()
        inventory_names = {_inventory_lookup_key(i.get("standardized_item", i.get("raw_phrase", ""))) for i in inventory}

        day_meals = []
        seen = set()
        needed_calories = target_calories
        for meal in candidates:
            if len(day_meals) >= 4:
                break
            name = meal.get("name")
            if name in seen:
                continue
            ingredients = [i for i in meal.get("ingredients", [])]
            has_match = any(_inventory_lookup_key(i) in inventory_names for i in ingredients)
            meal_cals = meal.get("calories", 0)
            if meal_cals > needed_calories and len(day_meals) >= 1:
                continue
            day_meals.append(meal)
            seen.add(name)
            needed_calories -= meal_cals
        preferences = state.get('preferences', '') or ''
        excluded = _excluded_terms(preferences)
        fallback = _fallback_day_meals(day_index, target_calories)
        meals = day_meals if day_meals else [m for m in fallback if _meal_allowed(m, excluded)]
    else:
        preferences = state.get('preferences', '') or ''
        excluded = _excluded_terms(preferences)
        fallback = _fallback_day_meals(day_index, target_calories)
        meals = [m for m in fallback if _meal_allowed(m, excluded)]

    total_calories = sum(m['calories'] for m in meals)
    total_protein = sum(m['macros']['protein'] for m in meals)
    total_carbs = sum(m['macros']['carbs'] for m in meals)

    return {
        'day': day_name,
        'meals': meals,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs
    }


def _fallback_day_meals(day_index: int, target_calories: int) -> list[dict]:
    meals = []
    for slot in _CORE_SLOTS:
        meals.append(_pick_meal(slot, day_index))
    meals.append(PROTEIN_SHAKE)
    core_with_shake = sum(m['calories'] for m in meals)
    extra = _pick_meal(EXTRA_SNACK_OPTIONS, day_index)
    if core_with_shake + extra['calories'] <= target_calories:
        meals.append(extra)
    return meals


# Per-serving quantities. Merge logic sums across days for correct weekly totals.
_INGREDIENT_MAP = {
    'Oatmeal': {'item': 'Oatmeal', 'quantity': 1, 'unit': 'cups', 'category': 'Grain'},
    'Mixed Berries': {'item': 'Mixed Berries', 'quantity': 0.5, 'unit': 'lbs', 'category': 'Fruit'},
    'Milk': {'item': 'Milk', 'quantity': 0.5, 'unit': 'cups', 'category': 'Dairy'},
    'Greek Yogurt': {'item': 'Greek Yogurt', 'quantity': 0.75, 'unit': 'cups', 'category': 'Dairy'},
    'Honey': {'item': 'Honey', 'quantity': 0.5, 'unit': 'oz', 'category': 'Pantry'},
    'Butter': {'item': 'Butter', 'quantity': 0.5, 'unit': 'tbsp', 'category': 'Dairy'},
    'Protein Powder': {'item': 'Protein Powder', 'quantity': 2, 'unit': 'scoops', 'category': 'Pantry'},
    'Almond Milk': {'item': 'Almond Milk', 'quantity': 0.5, 'unit': 'cups', 'category': 'Dairy'},
    'White Rice': {'item': 'White Rice', 'quantity': 1, 'unit': 'cups', 'category': 'Grain'},
    'Quinoa': {'item': 'Quinoa', 'quantity': 0.75, 'unit': 'cups', 'category': 'Grain'},
    'Soy Sauce': {'item': 'Soy Sauce', 'quantity': 1, 'unit': 'tbsp', 'category': 'Pantry'},
    'Olive Oil': {'item': 'Olive Oil', 'quantity': 1, 'unit': 'tbsp', 'category': 'Pantry'},
    'Mixed Nuts': {'item': 'Mixed Nuts', 'quantity': 0.25, 'unit': 'cups', 'category': 'Pantry'},
    'Cottage Cheese': {'item': 'Cottage Cheese', 'quantity': 0.5, 'unit': 'cups', 'category': 'Dairy'},
    # Protein (Chicken Thighs and Chicken Breast are distinct types per requirements)
    'Chicken Thighs': {'item': 'Chicken Thighs', 'quantity': 0.5, 'unit': 'lbs', 'category': 'Protein'},
    'Chicken Breast': {'item': 'Chicken Breast', 'quantity': 0.5, 'unit': 'lbs', 'category': 'Protein'},
    'Salmon': {'item': 'Salmon', 'quantity': 0.5, 'unit': 'lbs', 'category': 'Protein'},
    'Eggs': {'item': 'Eggs', 'quantity': 2, 'unit': 'count', 'category': 'Protein'},
    # Vegetables (fresh only, no frozen)
    'Mushrooms': {'item': 'Mushrooms', 'quantity': 1, 'unit': 'cups', 'category': 'Vegetable'},
    'Spinach': {'item': 'Spinach', 'quantity': 2, 'unit': 'cups', 'category': 'Vegetable'},
    'Bell Peppers': {'item': 'Bell Peppers', 'quantity': 1, 'unit': 'count', 'category': 'Vegetable'},
    'Green Beans': {'item': 'Green Beans', 'quantity': 1, 'unit': 'cups', 'category': 'Vegetable'},
    'Broccoli': {'item': 'Broccoli', 'quantity': 1, 'unit': 'cups', 'category': 'Vegetable'},
    # Fruit
    'Banana': {'item': 'Bananas', 'quantity': 1, 'unit': 'count', 'category': 'Fruit'},
}


def update_plan_in_state(state: dict, day_plans: list[dict], days_generated: list[str], updates: dict, inventory: list[dict] | None = None) -> dict:
    """Update state with new plan and consolidated grocery list."""
    state['plan'] = day_plans

    grocery_items = []
    for day_plan in day_plans:
        for meal in day_plan['meals']:
            for ingredient in meal.get('ingredients', []):
                mapped = _INGREDIENT_MAP.get(ingredient)
                if mapped:
                    grocery_items.append(mapped)

    merged: dict[str, dict] = {}
    for item in grocery_items:
        key = item['item']
        if key in merged:
            merged[key]['quantity'] += item['quantity']
        else:
            merged[key] = dict(item)

    inventory_names = set()
    if inventory:
        inventory_names = {_inventory_lookup_key(i.get("standardized_item", i.get("raw_phrase", ""))) for i in inventory}

    used = []
    unused = []
    for item in inventory or []:
        name = _inventory_lookup_key(item.get("standardized_item", item.get("raw_phrase", "")))
        if any(name == _inventory_lookup_key(i) for day in day_plans for meal in day['meals'] for i in meal.get('ingredients', [])):
            used.append(item)
        else:
            unused.append(item)

    supplemental = []
    grocery_list = list(merged.values())
    if inventory:
        for day in day_plans:
            for meal in day['meals']:
                for ingredient in meal.get('ingredients', []):
                    if _inventory_lookup_key(ingredient) in inventory_names:
                        continue
                    mapped = _INGREDIENT_MAP.get(ingredient)
                    if mapped:
                        supplemental.append(dict(mapped))
                    else:
                        supplemental.append({
                            'item': ingredient,
                            'quantity': 1,
                            'unit': 'count/whole',
                            'category': 'Other',
                        })

        merged_supplemental: dict[str, dict] = {}
        for item in supplemental:
            key = item['item']
            if key in merged_supplemental:
                merged_supplemental[key]['quantity'] += item['quantity']
            else:
                merged_supplemental[key] = dict(item)
        grocery_list = list(merged_supplemental.values())

    state['grocery_list'] = grocery_list

    if updates['ate_out'] and state['plan']:
        state['plan'][-1]['meals'] = []

    state['inventory_usage'] = {
        'used': used,
        'unused': unused,
        'supplemental': supplemental,
    }

    return state


_CATEGORY_ORDER = ['Dairy', 'Protein', 'Grain', 'Vegetable', 'Fruit', 'Pantry']


def format_plan_markdown(day_plans: list[dict], state: dict) -> str:
    """Format plan as Markdown code block."""
    lines = ["```markdown"]

    for day_plan in day_plans:
        lines.append(f"## {day_plan['day']} Meal Plan\n")
        lines.append("### Meals\n")
        lines.append("| Meal | Calories | Protein | Carbs | Fat |")
        lines.append("|-----|---------|--------|-------|-----|")

        for meal in day_plan['meals']:
            macros = meal.get('macros', {})
            lines.append(f"| {meal['name']} | {meal['calories']} | {macros.get('protein', 0)}g | {macros.get('carbs', 0)}g | {macros.get('fat', 0)}g |")

        lines.append(f"\n### Total Calories: {day_plan['total_calories']}  |  Total Protein: {day_plan['total_protein']}g  |  Total Carbs: {day_plan['total_carbs']}g")

    # Group grocery list by category
    grouped: dict[str, list[dict]] = {}
    for item in state['grocery_list']:
        cat = item.get('category', 'Other')
        grouped.setdefault(cat, []).append(item)

    lines.append("\n### Grocery List\n")

    for cat in _CATEGORY_ORDER:
        items = grouped.pop(cat, None)
        if not items:
            continue
        lines.append(f"**{cat}**")
        for item in items:
            quantity = item.get('quantity', 1)
            unit = item.get('unit', 'count/whole')
            lines.append(f"- {item.get('item', 'Unknown')}: {quantity} {unit}")
        lines.append("")

    for cat, items in grouped.items():
        lines.append(f"**{cat}**")
        for item in items:
            quantity = item.get('quantity', 1)
            unit = item.get('unit', 'count/whole')
            lines.append(f"- {item.get('item', 'Unknown')}: {quantity} {unit}")
        lines.append("")

    lines.append("```")

    return '\n'.join(lines)
