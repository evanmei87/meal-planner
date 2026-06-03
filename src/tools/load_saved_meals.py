"""Tool to load and display saved meals from meal-recipes.md."""
from pathlib import Path


def load_static_data() -> dict:
    """Load static markdown data files."""
    data_dir = Path(__file__).parent.parent / 'data'
    recipes_md = data_dir / 'meal-recipes.md'
    
    try:
        text = recipes_md.read_text()
    except FileNotFoundError:
        return {'recipes': ''}
    except PermissionError:
        print(f"Warning: Permission denied reading {recipes_md}")
        return {'recipes': ''}
    
    return {
        'recipes': text
    }


def load_saved_meals(filter_category: str = None, 
                     search_term: str = None) -> list:
    """
    Load saved meals from the recipes database.
    
    Args:
        filter_category: Filter meals by category (Breakfast/Lunch/Dinner/etc.)
        search_term: Search term to filter meals by name or ingredients
    
    Returns:
        List of meal dictionaries with metadata
    """
    static_data = load_static_data()
    recipes_content = static_data['recipes']
    meals = []
    
    if not recipes_content.strip():
        return meals
    
    lines = recipes_content.strip().split('\n')
    
    # Find the first data row (after header comments and separator)
    # Structure: header comments (3 lines) + blank line + separator row + data rows
    data_start_idx = 5
    
    for line in lines[data_start_idx:]:
        # Skip empty lines or separator rows
        if not line.strip() or line.strip().startswith('|:---:'):
            continue
            
        # Split by pipe, filter out empty strings
        parts = [p.strip() for p in line.split('|') if p.strip()]
        
        # Handle case where first field is empty (leading |)
        if not parts[0] and len(parts) > 1:
            parts = parts[1:]
        
        if len(parts) >= 7:
            meal = {
                'name': parts[0].strip(),
                'version': parts[1].strip(),
                'category': parts[2].strip(),
                'macros_raw': parts[3].strip(),
                'ingredients': [ing.strip() for ing in parts[4].strip().split(', ') if ing.strip()],
                'instructions': [inst.strip() for inst in parts[5].strip().split(';') if inst.strip()],
                'tags': [tag.strip() for tag in parts[6].strip().split(',') if tag.strip()]
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
                except (ValueError, IndexError) as e:
                    meal['macros'] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
                    print(f"Warning: Failed to parse macros for {meal['name']}: {e}")
            else:
                meal['macros'] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
            
            meals.append(meal)
    
    # Apply filters
    if filter_category:
        meals = [m for m in meals if m['category'].lower() == filter_category.lower()]
    
    if search_term:
        search_lower = search_term.lower()
        meals = [m for m in meals if 
                  search_lower in m['name'].lower() or 
                  any(search_lower in ing.lower() for ing in m['ingredients']) or
                  any(search_lower in tag.lower() for tag in m['tags'])]
    
    return meals


def format_meals_markdown(meals: list) -> str:
    """Format meals list as markdown table."""
    if not meals:
        return "No meals found."
    
    lines = []
    lines.append("## Saved Meals\n")
    lines.append("")
    lines.append("| Name | Version | Category | Macros | Instructions |")
    lines.append("|:---:|:---:|:---:|:---|:---:|")
    
    for meal in meals:
        macros_str = f"{meal['macros'].get('calories', 0)}|{meal['macros'].get('protein', 0)}|{meal['macros'].get('carbs', 0)}|{meal['macros'].get('fat', 0)}"
        lines.append(f"| {meal['name']} | {meal['version']} | {meal['category']} | {macros_str} | {meal['instructions']} |")
    
    return '\n'.join(lines)


def format_meals_cli(meals: list) -> str:
    """Format meals list for CLI output."""
    if not meals:
        return "No meals found."
    
    lines = []
    for meal in meals:
        lines.append(f"\n### {meal['name']}")
        lines.append(f"Category: {meal['category']}")
        lines.append(f"Version: {meal['version']}")
        lines.append(f"Macros: {meal['macros'].get('calories', 0)} cal, {meal['macros'].get('protein', 0)}g protein, {meal['macros'].get('carbs', 0)}g carbs, {meal['macros'].get('fat', 0)}g fat")
        lines.append(f"Ingredients: {', '.join(meal['ingredients'])}")
        lines.append(f"Instructions: {meal['instructions']}")
        if meal['tags']:
            lines.append(f"Tags: {', '.join(meal['tags'])}")
    
    return '\n'.join(lines)


def main():
    """CLI entry point for loading saved meals."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load and display saved meals')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--search', help='Search term')
    parser.add_argument('--format', choices=['markdown', 'cli'], default='cli', help='Output format')
    
    args = parser.parse_args()
    
    meals = load_saved_meals(filter_category=args.category, search_term=args.search)
    
    if args.format == 'markdown':
        print(format_meals_markdown(meals))
    else:
        print(format_meals_cli(meals))


if __name__ == '__main__':
    main()
