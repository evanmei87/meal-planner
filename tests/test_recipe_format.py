import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.recipe_format import parse_recipe_row, RECIPE_COLUMN_COUNT

DATA_ROW = (
    "| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 2 | 600,45,55,12 "
    "| Chicken Breast, White Rice | Cook chicken; Cook rice | high_protein, quick |"
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
    assert meal['ingredients'] == ['Chicken Breast', 'White Rice']
    assert meal['instructions'] == ['Cook chicken', 'Cook rice']
    assert meal['tags'] == ['high_protein', 'quick']


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
