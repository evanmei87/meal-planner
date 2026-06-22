"""Tool to add saved meals with auto-add functionality for new foods."""
import json
import re
from datetime import datetime
from pathlib import Path


def load_static_data() -> dict:
    """Load static data files: standardized food.csv plus specialty and recipes."""
    data_dir = Path(__file__).parent.parent / 'data'
    food_csv = data_dir / 'food.csv'
    specialty_md = data_dir / 'specialty-ingredients.md'
    recipes_md = data_dir / 'meal-recipes.md'

    return {
        'food_db': food_csv.read_text(),
        'specialty': specialty_md.read_text(),
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
        if line.strip().startswith('|:---:') or line.strip().startswith('| name'):
            continue
        if line.strip():
            parts = line.split('|')
            if len(parts) == 9:
                meal = {
                    'name': parts[1].strip(),
                    'version': parts[2].strip(),
                    'category': parts[3].strip(),
                    'macros_raw': parts[4].strip(),
                    'ingredients': [ing.strip() for ing in parts[5].strip().split(', ') if ing.strip()],
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


_SPECIALTY_CACHE = None


def _build_specialty_dict(specialty_content: str) -> dict:
    """Parse specialty-ingredients.md into a dict of ingredient_name -> macros."""
    parsed: dict[str, dict] = {}
    for line in specialty_content.split('\n'):
        if not line.strip().startswith('|'):
            continue
        if 'Ingredient' in line or 'Portion' in line:
            continue
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) < 6:
            continue
        name = parts[0].lower()
        if not name:
            continue
        try:
            parsed[name] = {
                'portion': parts[1],
                'calories': int(parts[2]),
                'protein': int(parts[3].rstrip('g')),
                'carbs': int(parts[4].rstrip('g')),
                'fat': int(parts[5].rstrip('g')),
            }
        except (ValueError, IndexError):
            parsed[name] = {'portion': parts[1] if len(parts) > 1 else '',
                            'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    return parsed


def invalidate_caches():
    """Invalidate cached specialty-ingredient data (call after adding new foods)."""
    global _SPECIALTY_CACHE
    _SPECIALTY_CACHE = None


def food_exists(food_name: str, specialty_content: str) -> bool:
    """Check if food exists in specialty-ingredients.md (case-insensitive, cached)."""
    global _SPECIALTY_CACHE
    if _SPECIALTY_CACHE is None:
        _SPECIALTY_CACHE = _build_specialty_dict(specialty_content)
    return food_name.lower().strip() in _SPECIALTY_CACHE


def get_food_macros(food_name: str, specialty_content: str) -> dict:
    """Get macros for a food from specialty-ingredients.md (cached)."""
    global _SPECIALTY_CACHE
    if _SPECIALTY_CACHE is None:
        _SPECIALTY_CACHE = _build_specialty_dict(specialty_content)
    return _SPECIALTY_CACHE.get(food_name.lower().strip())


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


def add_new_food(food_name: str, specialty_content: str, macros_data: dict) -> tuple:
    """Append a new ingredient row to specialty-ingredients.md."""
    specialty_path = Path(__file__).parent.parent / 'data' / 'specialty-ingredients.md'

    row = f"| {food_name}"
    row += " | " + macros_data.get('portion', '')
    row += " | " + str(macros_data.get('calories', 0))
    row += " | " + str(macros_data.get('protein', 0)) + "g"
    row += " | " + str(macros_data.get('carbs', 0)) + "g"
    row += " | " + str(macros_data.get('fat', 0)) + "g"
    row += " |"

    new_lines = specialty_content.split('\n')
    if new_lines and new_lines[-1].strip() != '':
        new_lines.append('')
    new_lines.append(row)

    specialty_path.write_text('\n'.join(new_lines))
    return True, food_name


def validate_macro_entry(portion: str, calories: str, protein: str, carbs: str, fat: str) -> tuple[bool, dict | None]:
    try:
        c = int(calories)
        p = int(protein)
        carb = int(carbs)
        f = int(fat)
    except (TypeError, ValueError):
        return False, None
    if not portion or c < 0 or p < 0 or carb < 0 or f < 0:
        return False, None
    return True, {
        'portion': portion,
        'calories': c,
        'protein': p,
        'carbs': carb,
        'fat': f,
    }


def append_specialty_ingredient(food_name: str, macros_data: dict, specialty_content: str) -> tuple[bool, str, str]:
    specialty_path = Path(__file__).parent.parent / 'data' / 'specialty-ingredients.md'
    row = f"| {food_name}"
    row += " | " + macros_data.get('portion', '')
    row += " | " + str(macros_data.get('calories', 0))
    row += " | " + str(macros_data.get('protein', 0)) + "g"
    row += " | " + str(macros_data.get('carbs', 0)) + "g"
    row += " | " + str(macros_data.get('fat', 0)) + "g"
    row += " |"
    new_lines = specialty_content.split('\n')
    if new_lines and new_lines[-1].strip() != '':
        new_lines.append('')
    new_lines.append(row)
    specialty_path.write_text('\n'.join(new_lines))
    return True, food_name, '\n'.join(new_lines)


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
        non_numeric = False
        try:
            int(macros.get('calories', 0))
            int(macros.get('protein', 0))
            int(macros.get('carbs', 0))
            int(macros.get('fat', 0))
        except (TypeError, ValueError):
            errors.append("All macro values (calories, protein, carbs, fat) must be numeric.")
            non_numeric = True

        if not non_numeric:
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
    
    specialty_content = static_data['specialty']
    recipes_content = static_data['recipes']

    newly_added = []

    # Process each ingredient
    for ingredient in ingredients:
        ingredient_clean = ingredient.strip()
        if not ingredient_clean:
            continue

        # Check if food exists in specialty-ingredients.md
        if not food_exists(ingredient_clean, specialty_content):
            if prompt_session:
                print(f"\nIngredient '{ingredient_clean}' not found in specialty ingredients.")
                macros_data = prompt_for_macros(prompt_session)

                # Add the new ingredient to specialty-ingredients.md
                success, food_name = add_new_food(ingredient_clean, specialty_content, macros_data)
                if success:
                    print(f"Added '{food_name}' to specialty ingredients.")
                    # Invalidate caches and reload content so subsequent lookups see the new food
                    invalidate_caches()
                    static_data = load_static_data()
                    specialty_content = static_data['specialty']
                else:
                    print(f"Warning: Failed to add '{ingredient_clean}' to specialty ingredients.")

                newly_added.append(ingredient_clean)
            else:
                # Auto-add without prompting
                newly_added.append(ingredient_clean)
        else:
            # Get existing macros if food exists
            existing_macros = get_food_macros(ingredient_clean, specialty_content)
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


def add_saved_meal_from_request(meal_data: dict, prompt_session=False) -> dict:
    """
    Add a saved meal from structured request data (for API use).
    
    Args:
        meal_data: Dictionary with keys:
            - name: Meal name
            - ingredients: List of ingredient names
            - macros: Dict with calories, protein, carbs, fat
            - instructions: List of instruction steps
            - category: Meal category (default: Dinner)
            - tags: List of tags (optional)
        prompt_session: Whether to prompt for new food properties (default: False for API)
    
    Returns:
        dict with success status and newly added foods
    """
    return add_saved_meal(
        meal_name=meal_data.get('name', ''),
        ingredients=meal_data.get('ingredients', []),
        macros=meal_data.get('macros', {}),
        instructions=meal_data.get('instructions', []),
        category=meal_data.get('category', 'Dinner'),
        tags=meal_data.get('tags', []),
        prompt_session=prompt_session
    )


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
