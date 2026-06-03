"""Tool to add saved meals with auto-add functionality for new foods."""
import json
import re
from datetime import datetime
from pathlib import Path


def load_static_data() -> dict:
    """Load static markdown data files."""
    data_dir = Path(__file__).parent.parent / 'data'
    foods_md = data_dir / 'foods.md'
    macros_md = data_dir / 'macros.md'
    recipes_md = data_dir / 'meal-recipes.md'
    
    return {
        'foods': foods_md.read_text(),
        'macros': macros_md.read_text(),
        'recipes': recipes_md.read_text()
    }


def save_recipes(recipes_content: str, recipes_path: Path) -> bool:
    """Save recipes to markdown file."""
    try:
        recipes_path.write_text(recipes_content)
        return True
    except Exception as e:
        print(f"Error saving recipes: {e}")
        return False


def load_recipes(recipes_content: str) -> list:
    """Parse recipes markdown file and return list of meal dicts."""
    meals = []
    
    if not recipes_content.strip():
        return meals
    
    lines = recipes_content.strip().split('\n')
    
    # Skip first 4 lines (header comments)
    for line in lines[4:]:
        if line.strip() and not line.strip().startswith('| name'):
            parts = line.split('|')
            if len(parts) == 8:
                meal = {
                    'name': parts[1].strip(),
                    'version': parts[2].strip(),
                    'category': parts[3].strip(),
                    'ingredients': [ing.strip() for ing in parts[4].strip().split(', ') if ing.strip()],
                    'macros_raw': parts[5].strip(),
                    'instructions': parts[6].strip(),
                    'tags': [tag.strip() for tag in parts[7].strip().split(',') if tag.strip()]
                }
                
                # Parse macros
                if meal['macros_raw']:
                    try:
                        macro_parts = meal['macros_raw'].split(',')
                        meal['macros'] = {
                            'calories': int(macro_parts[0]) if macro_parts[0] else 0,
                            'protein': int(macro_parts[1]) if macro_parts[1] else 0,
                            'carbs': int(macro_parts[2]) if macro_parts[2] else 0,
                            'fat': int(macro_parts[3]) if macro_parts[3] else 0
                        }
                    except (ValueError, IndexError):
                        meal['macros'] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
                else:
                    meal['macros'] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
                
                meals.append(meal)
    
    return meals


_FOODS_CACHE = None
_MACROS_CACHE = None


def _build_foods_set(foods_content: str) -> set:
    """Build a set of food names for O(1) lookups."""
    foods = set()
    for line in foods_content.split('\n'):
        if line.strip().startswith('|') and 'Food' not in line:
            food = line.split('|')[1].strip().lower()
            if food:
                foods.add(food)
    return foods


def _build_macros_dict(macros_content: str) -> dict:
    """Build a dict of food -> macros for O(1) lookups."""
    macros_dict = {}
    for line in macros_content.split('\n'):
        if line.strip().startswith('|') and 'Food' not in line:
            parts = line.split('|')
            if len(parts) >= 5:
                food = parts[1].strip().lower()
                if food:
                    try:
                        macros_dict[food] = {
                            'portion': parts[2].strip(),
                            'calories': int(parts[3].strip()),
                            'protein': int(parts[4].strip()),
                            'carbs': int(parts[5].strip()),
                            'fat': int(parts[6].strip())
                        }
                    except (ValueError, IndexError):
                        macros_dict[food] = {'portion': '', 'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    return macros_dict


def invalidate_caches():
    """Invalidate cached food and macro data (call after adding new foods)."""
    global _FOODS_CACHE, _MACROS_CACHE
    _FOODS_CACHE = None
    _MACROS_CACHE = None


def food_exists(food_name: str, foods_content: str) -> bool:
    """Check if food exists in foods.md (case-insensitive, cached)."""
    global _FOODS_CACHE
    if _FOODS_CACHE is None:
        _FOODS_CACHE = _build_foods_set(foods_content)
    return food_name.lower().strip() in _FOODS_CACHE


def get_food_macros(food_name: str, macros_content: str) -> dict:
    """Get macros for a food from macros.md (cached)."""
    global _MACROS_CACHE
    if _MACROS_CACHE is None:
        _MACROS_CACHE = _build_macros_dict(macros_content)
    return _MACROS_CACHE.get(food_name.lower().strip())


def prompt_for_food_properties(food_name: str, foods_content: str, prompt_session) -> dict:
    """Prompt user for new food properties with validation."""
    print(f"\nNew food detected: {food_name}")
    print("This food will be added to your food database.")
    print("\n--- Food Properties ---")
    
    while True:
        category = input(f"Category (Protein/Grain/Vegetable/etc.): ").strip()
        if category:
            break
        print("Category is required. Please enter a valid food category.")
    
    preparation = input(f"Preparation method: ").strip() or "Standard"
    notes = input(f"Notes: ").strip() or ""
    
    return {
        'food_name': food_name,
        'category': category,
        'preparation': preparation,
        'notes': notes
    }


def prompt_for_macros(prompt_session) -> dict:
    """Prompt user for macro data with validation."""
    print("\n--- Nutritional Data ---")
    print("Format: portion|calories|protein(g)|carbs(g)|fat(g)")
    
    while True:
        macro_input = input("Enter macro data: ").strip()
        
        macro_parts = macro_input.split('|')
        if len(macro_parts) >= 5:
            try:
                portion = macro_parts[0].strip()
                calories = int(macro_parts[1])
                protein = int(macro_parts[2])
                carbs = int(macro_parts[3])
                fat = int(macro_parts[4])
                
                if not portion:
                    print("Portion size is required (e.g., '1 cup', '100g').")
                    continue
                
                if calories < 0 or protein < 0 or carbs < 0 or fat < 0:
                    print("Macro values cannot be negative.")
                    continue
                
                return {
                    'portion': portion,
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fat': fat
                }
            except (ValueError, IndexError):
                pass
        
        print("Invalid format. Use: portion|calories|protein|carbs|fat  (e.g., 1 cup|200|20|30|10)")


def add_new_food(food_name: str, foods_content: str, macros_content: str, 
                 food_props: dict, macros_data: dict) -> tuple:
    """Add new food to foods.md and macros.md."""
    foods_path = Path(__file__).parent.parent / 'data' / 'foods.md'
    macros_path = Path(__file__).parent.parent / 'data' / 'macros.md'
    
    # Build the new food row: food_name | category | preparation | notes
    food_row = food_props.get('food_name', food_name)
    food_row += " | " + food_props.get('category', 'Other')
    food_row += " | " + food_props.get('preparation', 'Standard')
    food_row += " | " + food_props.get('notes', '')
    
    # Find the last table row in foods.md to insert after it
    lines = foods_content.split('\n')
    last_table_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('|') and 'Food' not in line:
            last_table_idx = i
    # Insert after the last table row (or after line 2 if no rows exist)
    insert_at = (last_table_idx + 1) if last_table_idx is not None else 3
    lines.insert(insert_at, "| " + food_row + " |")
    
    # Build and append new macros row
    macros_row = food_props.get('food_name', food_name)
    macros_row += " | " + macros_data.get('portion', '')
    macros_row += " | " + str(macros_data.get('calories', 0))
    macros_row += " | " + str(macros_data.get('protein', 0)) + "g"
    macros_row += " | " + str(macros_data.get('carbs', 0)) + "g"
    macros_row += " | " + str(macros_data.get('fat', 0)) + "g"
    
    # Append to the end of macros content
    macros_lines = macros_content.split('\n')
    macros_lines.append("| " + macros_row + " |")
    
    # Write both files
    foods_path.write_text('\n'.join(lines))
    macros_path.write_text('\n'.join(macros_lines))
    
    return True, food_props.get('food_name', food_name)


def validate_meal_params(meal_name: str, ingredients: list,
                          macros: dict, instructions: list) -> list:
    """Validate meal parameters and return list of error messages."""
    errors = []
    
    if not meal_name or not meal_name.strip():
        errors.append("Meal name is required and cannot be empty.")
    
    if not ingredients or all(not ing.strip() for ing in ingredients):
        errors.append("At least one ingredient is required.")
    
    if not instructions or all(not inst.strip() for inst in instructions):
        errors.append("At least one instruction step is required.")
    
    if macros:
        try:
            int(macros.get('calories', 0))
            int(macros.get('protein', 0))
            int(macros.get('carbs', 0))
            int(macros.get('fat', 0))
        except (TypeError, ValueError):
            errors.append("All macro values (calories, protein, carbs, fat) must be numeric.")
    
        if macros.get('calories', 0) < 0 or macros.get('protein', 0) < 0 \
           or macros.get('carbs', 0) < 0 or macros.get('fat', 0) < 0:
            errors.append("Macro values cannot be negative.")
    
    return errors


def add_saved_meal(meal_name: str, ingredients: list, 
                   macros: dict, instructions: list, 
                   category: str = "Dinner", tags: list = None, 
                   prompt_session=True) -> dict:
    """
    Add a saved meal to the recipes database.
    
    Args:
        meal_name: Name of the meal
        ingredients: List of ingredient food names
        macros: Dictionary with keys: calories, protein, carbs, fat
        instructions: List of instruction steps
        category: Meal category (Breakfast/Lunch/Dinner/etc.)
        tags: List of tags for the meal
        prompt_session: Whether to prompt for new food properties
    
    Returns:
        dict with success status and newly added foods
    """
    # Validate inputs
    errors = validate_meal_params(meal_name, ingredients, macros, instructions)
    if errors:
        return {
            'success': False,
            'meal_name': meal_name,
            'newly_added': [],
            'category': category,
            'message': f"Validation failed: {'; '.join(errors)}"
        }
    
    try:
        static_data = load_static_data()
    except FileNotFoundError as e:
        return {
            'success': False,
            'meal_name': meal_name,
            'newly_added': [],
            'category': category,
            'message': f"Data file not found: {e}"
        }
    except PermissionError as e:
        return {
            'success': False,
            'meal_name': meal_name,
            'newly_added': [],
            'category': category,
            'message': f"Permission denied reading data file: {e}"
        }
    
    foods_content = static_data['foods']
    macros_content = static_data['macros']
    recipes_content = static_data['recipes']
    
    newly_added = []
    
    # Process each ingredient
    for ingredient in ingredients:
        ingredient_clean = ingredient.strip()
        if not ingredient_clean:
            continue
        
        # Check if food exists
        if not food_exists(ingredient_clean, foods_content):
            if prompt_session:
                print(f"\nIngredient '{ingredient_clean}' not found in food database.")
                food_props = prompt_for_food_properties(ingredient_clean, foods_content, prompt_session)
                macros_data = prompt_for_macros(prompt_session)
                
                # Add the new food to both foods.md and macros.md
                success, food_name = add_new_food(ingredient_clean, foods_content, macros_content, food_props, macros_data)
                if success:
                    print(f"Added '{food_name}' to food database.")
                    # Invalidate caches and reload content so subsequent lookups see the new food
                    invalidate_caches()
                    static_data = load_static_data()
                    foods_content = static_data['foods']
                    macros_content = static_data['macros']
                else:
                    print(f"Warning: Failed to add '{ingredient_clean}' to food database.")
                
                newly_added.append(ingredient_clean)
            else:
                # Auto-add without prompting
                macros_data = {
                    'portion': '',
                    'calories': macros.get('calories', 0),
                    'protein': macros.get('protein', 0),
                    'carbs': macros.get('carbs', 0),
                    'fat': macros.get('fat', 0)
                }
                newly_added.append(ingredient_clean)
        else:
            # Get existing macros if food exists
            existing_macros = get_food_macros(ingredient_clean, macros_content)
            if existing_macros and all(existing_macros.values()):
                macros = existing_macros
            else:
                newly_added.append(ingredient_clean)
    
    # Create new row for meal
    timestamp = datetime.now().isoformat()
    
    ingredients_str = ', '.join(ingredient.strip() for ingredient in ingredients if ingredient.strip())
    macros_str = f"{macros.get('calories', 0)},{macros.get('protein', 0)},{macros.get('carbs', 0)},{macros.get('fat', 0)}"
    instructions_str = '; '.join(instructions) if instructions else 'Not specified'
    
    if not tags:
        tags = []
    tags_str = ', '.join(tags) if tags else ''
    
    # Format tags with pipe separator for markdown
    tags_formatted = ','.join(str(tag) for tag in tags) if tags else ''
    
    new_row = f"| {meal_name} | {timestamp} | {category} | {macros_str} | {ingredients_str} | {instructions_str} | {tags_formatted} |"
    
    # Append to recipes
    recipes_lines = recipes_content.split('\n')
    recipes_content = '\n'.join(recipes_lines) + '\n' + new_row
    
    save_recipes(recipes_content, Path(__file__).parent.parent / 'data' / 'meal-recipes.md')
    
    result = {
        'success': True,
        'meal_name': meal_name,
        'newly_added': newly_added,
        'category': category
    }
    
    if newly_added:
        result['message'] = f"Meal '{meal_name}' added successfully. New foods: {', '.join(newly_added)}"
    else:
        result['message'] = f"Meal '{meal_name}' added successfully."
    
    return result


def main():
    """CLI entry point for adding saved meals."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add a saved meal to the recipe database')
    parser.add_argument('--name', required=True, help='Name of the meal')
    parser.add_argument('--ingredients', required=True, help='Comma-separated list of ingredients')
    parser.add_argument('--macros', required=True, help='Macros in format: calories|protein|carbs|fat')
    parser.add_argument('--instructions', required=True, help='Instructions as semicolon-separated steps')
    parser.add_argument('--category', default='Dinner', help='Meal category')
    parser.add_argument('--tags', default='', help='Comma-separated tags')
    
    args = parser.parse_args()
    
    # Parse ingredients
    ingredients = [ing.strip() for ing in args.ingredients.split(',')]
    
    # Parse macros
    macro_parts = [m.strip() for m in args.macros.split('|')]
    macros = {
        'calories': int(macro_parts[0]) if macro_parts[0] else 0,
        'protein': int(macro_parts[1]) if macro_parts[1] else 0,
        'carbs': int(macro_parts[2]) if macro_parts[2] else 0,
        'fat': int(macro_parts[3]) if macro_parts[3] else 0
    }
    
    # Parse instructions
    instructions = [inst.strip() for inst in args.instructions.split(';') if inst.strip()]
    
    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()] if args.tags else []
    
    # Add meal
    result = add_saved_meal(
        meal_name=args.name,
        ingredients=ingredients,
        macros=macros,
        instructions=instructions,
        category=args.category,
        tags=tags,
        prompt_session=True  # Enable prompting for new foods
    )
    
    print(result['message'])
    if result['newly_added']:
        print(f"New foods added: {', '.join(result['newly_added'])}")


if __name__ == '__main__':
    main()
