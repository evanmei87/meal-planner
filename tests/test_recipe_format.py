import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.recipe_format import parse_recipe_row, RECIPE_COLUMN_COUNT, _parse_ingredient

DATA_ROW = (
    "| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 2 | 600,45,55,12 "
    "| Chicken Breast:6 oz:280:38:0:8, White Rice:1 cup:205:4:45:0 | Cook chicken; Cook rice | high_protein, quick |"
)
HEADER_ROW = "| name | version | category | servings | macros | ingredients | instructions | tags |"
SEPARATOR_ROW = "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"


def test_column_count_is_eight():
    assert RECIPE_COLUMN_COUNT == 8


def test_parses_all_fields():
    meal = parse_recipe_row(DATA_ROW)
    assert meal['name'] == 'Chicken Bowl'
    assert meal['version'] == '2024-01-01T00:00:00'
    assert meal['category'] == 'Dinner'
    assert meal['servings'] == 2
    assert meal['macros'] == {'calories': 600, 'protein': 45, 'carbs': 55, 'fat': 12}
    assert meal['ingredients'] == [
        {'name': 'Chicken Breast', 'serving': '6 oz', 'calories': 280, 'protein': 38, 'carbs': 0, 'fat': 8},
        {'name': 'White Rice', 'serving': '1 cup', 'calories': 205, 'protein': 4, 'carbs': 45, 'fat': 0},
    ]
    assert meal['instructions'] == ['Cook chicken', 'Cook rice']
    assert meal['tags'] == ['high_protein', 'quick']


# --- structured ingredient parsing ---

def test_parse_ingredient_full():
    assert _parse_ingredient('Salmon:6 oz:350:39:0:21') == {
        'name': 'Salmon', 'serving': '6 oz', 'calories': 350, 'protein': 39, 'carbs': 0, 'fat': 21,
    }


def test_parse_ingredient_bare_name_defaults_rest():
    assert _parse_ingredient('Apple') == {
        'name': 'Apple', 'serving': '', 'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0,
    }


def test_parse_ingredient_non_numeric_macro_defaults_to_zero():
    assert _parse_ingredient('Apple:1 medium:abc:1:25:0') == {
        'name': 'Apple', 'serving': '1 medium', 'calories': 0, 'protein': 1, 'carbs': 25, 'fat': 0,
    }


def test_multiple_structured_ingredients_in_one_row():
    row = (
        "| Bowl | v1 | Dinner | 1 | 400,20,40,10 "
        "| Tofu:6 oz:130:15:3:8, Broccoli:1 cup:55:4:11:1 | Cook | vegan |"
    )
    meal = parse_recipe_row(row)
    assert meal['ingredients'] == [
        {'name': 'Tofu', 'serving': '6 oz', 'calories': 130, 'protein': 15, 'carbs': 3, 'fat': 8},
        {'name': 'Broccoli', 'serving': '1 cup', 'calories': 55, 'protein': 4, 'carbs': 11, 'fat': 1},
    ]


def test_header_row_returns_none():
    assert parse_recipe_row(HEADER_ROW) is None


def test_separator_row_returns_none():
    assert parse_recipe_row(SEPARATOR_ROW) is None


def test_blank_or_nonrow_returns_none():
    assert parse_recipe_row("") is None
    assert parse_recipe_row("   ") is None
    assert parse_recipe_row("<!-- comment -->") is None


def test_empty_tags_cell_keeps_columns_aligned():
    row = "| Plain | v1 | Snack | 1 | 100,5,10,2 | Apple | Eat it | |"
    meal = parse_recipe_row(row)
    assert meal['name'] == 'Plain'
    assert meal['tags'] == []
    assert meal['servings'] == 1


def test_bad_servings_defaults_to_one():
    row = "| X | v1 | Snack | abc | 100,5,10,2 | Apple | Eat | snack |"
    assert parse_recipe_row(row)['servings'] == 1


def test_wrong_column_count_returns_none():
    assert parse_recipe_row("| only | three | cols |") is None
