"""Tool to search and filter saved meals."""
from pathlib import Path

from .recipe_format import parse_recipe_row


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
    
    for line in recipes_content.strip().split('\n'):
        meal = parse_recipe_row(line)
        if meal is not None:
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


def search_meals(criteria: dict) -> list:
    """
    Search and filter meals based on criteria.
    
    Args:
        criteria: Dictionary containing filter options:
            - category: Filter by category
            - min_cal / max_cal: Calorie range
            - min_prot / max_prot: Protein range
            - min_carb / max_carb: Carbs range
            - min_fat / max_fat: Fat range
            - ingredient: Filter by ingredient presence
            - tag: Filter by tag
            - search_term: Search term for name/ingredients/tags
    
    Returns:
        List of meal dictionaries matching criteria
    """
    meals = load_saved_meals()
    
    # Apply category filter
    if 'category' in criteria:
        meals = [m for m in meals if m['category'].lower() == criteria['category'].lower()]
    
    # Apply search term filter
    if 'search_term' in criteria:
        search_lower = criteria['search_term'].lower()
        meals = [m for m in meals if 
                  search_lower in m['name'].lower() or 
                  any(search_lower in ing.lower() for ing in m['ingredients']) or
                  any(search_lower in tag.lower() for tag in m['tags'])]
    
    # Apply macro range filters
    if 'min_cal' in criteria:
        meals = [m for m in meals if m['macros']['calories'] >= criteria['min_cal']]
    
    if 'max_cal' in criteria:
        meals = [m for m in meals if m['macros']['calories'] <= criteria['max_cal']]
    
    if 'min_prot' in criteria:
        meals = [m for m in meals if m['macros']['protein'] >= criteria['min_prot']]
    
    if 'max_prot' in criteria:
        meals = [m for m in meals if m['macros']['protein'] <= criteria['max_prot']]
    
    if 'min_carb' in criteria:
        meals = [m for m in meals if m['macros']['carbs'] >= criteria['min_carb']]
    
    if 'max_carb' in criteria:
        meals = [m for m in meals if m['macros']['carbs'] <= criteria['max_carb']]
    
    if 'min_fat' in criteria:
        meals = [m for m in meals if m['macros']['fat'] >= criteria['min_fat']]
    
    if 'max_fat' in criteria:
        meals = [m for m in meals if m['macros']['fat'] <= criteria['max_fat']]
    
    # Apply ingredient filter
    if 'ingredient' in criteria:
        ingredient_lower = criteria['ingredient'].lower()
        meals = [m for m in meals if any(ingredient_lower in ing.lower() for ing in m['ingredients'])]
    
    # Apply tag filter
    if 'tag' in criteria:
        tag_lower = criteria['tag'].lower()
        meals = [m for m in meals if any(tag_lower in tag.lower() for tag in m['tags'])]
    
    return meals


def main():
    """CLI entry point for searching meals."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Search and filter saved meals')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--min-cal', type=int, help='Minimum calories')
    parser.add_argument('--max-cal', type=int, help='Maximum calories')
    parser.add_argument('--min-prot', type=int, help='Minimum protein')
    parser.add_argument('--max-prot', type=int, help='Maximum protein')
    parser.add_argument('--min-carb', type=int, help='Minimum carbs')
    parser.add_argument('--max-carb', type=int, help='Maximum carbs')
    parser.add_argument('--min-fat', type=int, help='Minimum fat')
    parser.add_argument('--max-fat', type=int, help='Maximum fat')
    parser.add_argument('--ingredient', help='Filter by ingredient')
    parser.add_argument('--tag', help='Filter by tag')
    parser.add_argument('--search', help='Search term')
    parser.add_argument('--sort-by', choices=['calories', 'protein', 'name'], help='Sort by field')
    parser.add_argument('--sort-order', choices=['asc', 'desc'], default='asc', help='Sort order')
    
    args = parser.parse_args()
    
    criteria = {
        'category': args.category,
        'min_cal': args.min_cal,
        'max_cal': args.max_cal,
        'min_prot': args.min_prot,
        'max_prot': args.max_prot,
        'min_carb': args.min_carb,
        'max_carb': args.max_carb,
        'min_fat': args.min_fat,
        'max_fat': args.max_fat,
        'ingredient': args.ingredient,
        'tag': args.tag,
        'search_term': args.search,
        'sort_by': args.sort_by,
        'sort_order': args.sort_order
    }
    
    # Remove None values
    criteria = {k: v for k, v in criteria.items() if v is not None}
    
    results = search_meals(criteria)
    
    if results:
        print(f"Found {len(results)} meal(s):\n")
        for meal in results:
            print(f"### {meal['name']}")
            print(f"Category: {meal['category']}")
            print(f"Macros: {meal['macros']['calories']} cal, {meal['macros']['protein']}g protein, {meal['macros']['carbs']}g carbs, {meal['macros']['fat']}g fat")
            print(f"I n g r e d i e n t s: {', '.join(meal['ingredients'])}")
            print(f"Instructions: {meal['instructions']}")
            if meal['tags']:
                print(f"Tags: {', '.join(meal['tags'])}")
            print()
    else:
        print("No meals found matching criteria.")


if __name__ == '__main__':
    main()
