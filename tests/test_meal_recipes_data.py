import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.load_saved_meals import load_saved_meals


def test_all_recipes_have_servings_and_multistep_instructions():
    meals = load_saved_meals()
    assert len(meals) == 5
    for meal in meals:
        assert meal['servings'] >= 1, f"{meal['name']} missing servings"
        assert len(meal['instructions']) >= 3, (
            f"{meal['name']} should have step-by-step instructions"
        )
        assert meal['macros']['calories'] > 0


def test_known_meal_still_loads():
    meals = load_saved_meals()
    names = {m['name'] for m in meals}
    assert 'Salmon & Quinoa' in names
