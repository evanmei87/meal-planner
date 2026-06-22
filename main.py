import sys
from pathlib import Path
import json
import argparse

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tools.generate_plan import generate_meal_plan, load_state
from tools.update_state import update_state
from tools.grocery_inventory import get_inventory, add_inventory_items, add_unmatched_items, clear_inventory, format_inventory_for_cli
from tools.food_processor import parse_ingredients, get_ingredient_metadata


def groceries_add_text(args):
    """Parse grocery text and merge into inventory."""
    if not args.text:
        print("Usage: groceries add --text \"I got two pounds boneless chicken thighs, spinach, and half a pound of salmon.\"")
        return

    ingredients = parse_ingredients(args.text)
    results = []
    to_save = []
    unmatched = []
    for item in ingredients:
        meta = get_ingredient_metadata(item)
        results.append(meta)
        if meta.get("should_auto_save") and meta.get("source") == "corgis":
            to_save.append(meta)
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
    if args.generate:
        state_path = 'src/state/state.json'
        plan = generate_meal_plan(state_path, 'Generate 7-day meal plan')
        print(plan)


def groceries_list(_args):
    print(format_inventory_for_cli())


def groceries_clear(_args):
    clear_inventory()
    print("Grocery inventory cleared.")


def add_saved_meal_cli(args):
    """CLI handler for adding saved meals."""
    from tools.add_saved_meal import add_saved_meal

    ingredients = [ing.strip() for ing in args.ingredients.split(',')]

    if args.macros and '|' in args.macros:
        macro_parts = [m.strip() for m in args.macros.split('|')]
        macros = {
            'calories': int(macro_parts[0]) if macro_parts[0] else 0,
            'protein': int(macro_parts[1]) if macro_parts[1] else 0,
            'carbs': int(macro_parts[2]) if macro_parts[2] else 0,
            'fat': int(macro_parts[3]) if macro_parts[3] else 0
        }
    else:
        macros = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}

    instructions = [inst.strip() for inst in args.instructions.split(';') if inst.strip()]

    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()] if args.tags else []

    result = add_saved_meal(
        meal_name=args.name,
        ingredients=ingredients,
        macros=macros,
        instructions=instructions,
        category=args.category,
        tags=tags,
        prompt_session=True
    )

    print(result['message'])
    if result['newly_added']:
        print(f"New foods added: {', '.join(result['newly_added'])}")


def list_meals_cli(args):
    """CLI handler for listing/searching meals."""
    from tools.load_saved_meals import load_saved_meals

    meals = load_saved_meals(filter_category=args.category, search_term=args.search)

    if not meals:
        print("No meals found.")
        return

    print(f"\n## Saved Meals ({len(meals)} total)\n")
    print(f"| Name | Category | Macros |")
    print(f"|------|----------|--------|")
    for meal in meals:
        macros = meal['macros']
        print(f"| {meal['name']} | {meal['category']} | {macros['calories']} cal, {macros['protein']}g prot, {macros['carbs']}g carb, {macros['fat']}g fat |")

    if args.format == 'verbose':
        print()
        for meal in meals:
            print(f"\n### {meal['name']}")
            print(f"Category: {meal['category']}")
            print(f"Version: {meal['version']}")
            print(f"Ingredients: {', '.join(meal['ingredients'])}")
            print(f"Instructions: {meal['instructions']}")
            if meal['tags']:
                print(f"Tags: {', '.join(meal['tags'])}")


def search_meals_cli(args):
    """CLI handler for advanced meal search."""
    from tools.search_meals import search_meals

    criteria = {}

    if args.category:
        criteria['category'] = args.category

    if args.search:
        criteria['search_term'] = args.search

    if args.min_cal is not None:
        criteria['min_cal'] = args.min_cal

    if args.max_cal is not None:
        criteria['max_cal'] = args.max_cal

    if args.min_prot is not None:
        criteria['min_prot'] = args.min_prot

    if args.max_prot is not None:
        criteria['max_prot'] = args.max_prot

    if args.min_carb is not None:
        criteria['min_carb'] = args.min_carb

    if args.max_carb is not None:
        criteria['max_carb'] = args.max_carb

    if args.min_fat is not None:
        criteria['min_fat'] = args.min_fat

    if args.max_fat is not None:
        criteria['max_fat'] = args.max_fat

    if args.ingredient:
        criteria['ingredient'] = args.ingredient

    if args.tag:
        criteria['tag'] = args.tag

    results = search_meals(criteria)

    if results:
        print(f"\nFound {len(results)} meal(s):\n")
        for meal in results:
            print(f"### {meal['name']}")
            print(f"Category: {meal['category']}")
            print(f"Macros: {meal['macros']['calories']} cal, {meal['macros']['protein']}g protein, {meal['macros']['carbs']}g carbs, {meal['macros']['fat']}g fat")
            print(f"Ingredients: {', '.join(meal['ingredients'])}")
            print(f"Instructions: {meal['instructions']}")
            if meal['tags']:
                print(f"Tags: {', '.join(meal['tags'])}")
            print()
    else:
        print("No meals found matching criteria.")


def generate_plan_cli(args):
    """CLI handler for generating meal plan."""
    state_path = 'src/state/state.json'
    plan = generate_meal_plan(state_path, 'Generate 7-day meal plan')
    print(plan)
    print("\nCurrent state:")
    print(json.dumps(load_state(state_path), indent=2))


def main():
    """Main entry point for meal planner with saved meals support."""
    parser = argparse.ArgumentParser(description='Meal Planner with Saved Meals')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    add_parser = subparsers.add_parser('add', help='Add a saved meal')
    add_parser.add_argument('--name', required=True, help='Name of the meal')
    add_parser.add_argument('--ingredients', required=True, help='Comma-separated list of ingredients')
    add_parser.add_argument('--macros', required=True, help='Macros in format: calories|protein|carbs|fat')
    add_parser.add_argument('--instructions', required=True, help='Instructions as semicolon-separated steps')
    add_parser.add_argument('--category', default='Dinner', help='Meal category')
    add_parser.add_argument('--tags', default='', help='Comma-separated tags')
    add_parser.set_defaults(func=add_saved_meal_cli)

    list_parser = subparsers.add_parser('list', help='List all saved meals')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--search', help='Search term')
    list_parser.add_argument('--format', choices=['compact', 'verbose'], default='compact', help='Output format')
    list_parser.set_defaults(func=list_meals_cli)

    search_parser = subparsers.add_parser('search', help='Search saved meals')
    search_parser.add_argument('--category', help='Filter by category')
    search_parser.add_argument('--search', help='Search term')
    search_parser.add_argument('--min-cal', type=int, help='Minimum calories')
    search_parser.add_argument('--max-cal', type=int, help='Maximum calories')
    search_parser.add_argument('--min-prot', type=int, help='Minimum protein')
    search_parser.add_argument('--max-prot', type=int, help='Maximum protein')
    search_parser.add_argument('--min-carb', type=int, help='Minimum carbs')
    search_parser.add_argument('--max-carb', type=int, help='Maximum carbs')
    search_parser.add_argument('--min-fat', type=int, help='Minimum fat')
    search_parser.add_argument('--max-fat', type=int, help='Maximum fat')
    search_parser.add_argument('--ingredient', help='Filter by ingredient')
    search_parser.add_argument('--tag', help='Filter by tag')
    search_parser.set_defaults(func=search_meals_cli)

    gen_parser = subparsers.add_parser('generate', help='Generate meal plan')
    gen_parser.set_defaults(func=generate_plan_cli)

    groceries_parser = subparsers.add_parser('groceries', help='Manage grocery inventory')
    groceries_sub = groceries_parser.add_subparsers(dest='groceries_command')

    ga = groceries_sub.add_parser('add', help='Add groceries from natural language')
    ga.add_argument('--text', required=True, help='Natural language grocery description')
    ga.add_argument('--generate', action='store_true', help='Generate plan after adding')
    ga.set_defaults(func=groceries_add_text)

    gl = groceries_sub.add_parser('list', help='List grocery inventory')
    gl.set_defaults(func=groceries_list)

    gc = groceries_sub.add_parser('clear', help='Clear grocery inventory')
    gc.set_defaults(func=groceries_clear)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    elif args.command == 'groceries' and hasattr(args, 'groceries_command'):
        if args.groceries_command == 'add':
            groceries_add_text(args)
        elif args.groceries_command == 'list':
            groceries_list(args)
        elif args.groceries_command == 'clear':
            groceries_clear(args)
        else:
            groceries_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
