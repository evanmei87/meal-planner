"""Shared parser for a single `meal-recipes.md` table row.

Column order: name | version | category | servings | macros | ingredients | instructions | tags
"""

RECIPE_COLUMN_COUNT = 8


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split('|')]


def _is_separator(cells: list[str]) -> bool:
    return all(cell and set(cell) <= set(':-') for cell in cells)


def _parse_macros(raw: str) -> dict:
    parts = raw.split(',')

    def value(index: int) -> int:
        return int(parts[index]) if len(parts) > index and parts[index].strip() else 0

    try:
        return {
            'calories': value(0),
            'protein': value(1),
            'carbs': value(2),
            'fat': value(3),
        }
    except ValueError:
        return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}


def _parse_servings(raw: str) -> int:
    try:
        servings = int(raw)
    except (ValueError, TypeError):
        return 1
    return servings if servings >= 1 else 1


def parse_recipe_row(line: str) -> dict | None:
    """Parse one markdown table row into a meal dict, or None if not a data row."""
    if not line.strip().startswith('|'):
        return None

    cells = _split_row(line)
    if len(cells) != RECIPE_COLUMN_COUNT:
        return None
    if _is_separator(cells):
        return None
    if cells[0].lower() == 'name':  # header row
        return None

    macros_raw = cells[4]
    return {
        'name': cells[0],
        'version': cells[1],
        'category': cells[2],
        'servings': _parse_servings(cells[3]),
        'macros_raw': macros_raw,
        'macros': _parse_macros(macros_raw),
        'ingredients': [item.strip() for item in cells[5].split(',') if item.strip()],
        'instructions': [step.strip() for step in cells[6].split(';') if step.strip()],
        'tags': [tag.strip() for tag in cells[7].split(',') if tag.strip()],
    }
