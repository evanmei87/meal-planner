from pydantic import BaseModel
from src.tools.llm_agent import GeminiAgent

KNOWN_MEAL_TERMS = [
    # meal names
    "oatmeal with berries", "oatmeal with greek yogurt",
    "oatmeal with scrambled eggs", "oatmeal and protein shake",
    "chicken thigh stir-fry with rice", "salmon rice bowl",
    "grilled chicken rice plate", "salmon quinoa bowl",
    "chicken breast with quinoa", "salmon with quinoa and spinach",
    "protein shake (2 scoops)",
    "greek yogurt with nuts", "cottage cheese", "hard-boiled eggs",
    # ingredients
    "oatmeal", "mixed berries", "milk", "greek yogurt", "honey",
    "eggs", "butter", "protein powder", "almond milk", "white rice",
    "quinoa", "soy sauce", "olive oil", "mixed nuts", "cottage cheese",
    "chicken thighs", "chicken breast", "salmon",
    "mushrooms", "spinach", "bell peppers", "green beans", "broccoli", "banana",
]

_KNOWN_TERMS_TEXT = ", ".join(KNOWN_MEAL_TERMS)


class _PreferenceExclusions(BaseModel):
    excluded_terms: list[str]


def normalize_preferences(preferences: str) -> list[str]:
    """Return lowercase exclusion terms derived from a natural-language preferences string.

    Calls Gemini to handle misspellings, synonyms, and category terms.
    Falls back to simple 'no X' keyword parsing on any error.
    """
    if not preferences or not preferences.strip():
        return []

    prompt = (
        f'The user has these dietary preferences: "{preferences}"\n\n'
        "Identify which items from the known list below should be EXCLUDED based on "
        "the user's preferences. Consider misspellings, synonyms, and category terms "
        '(e.g. "no dairy" → exclude milk, butter, greek yogurt, almond milk; '
        '"no poultry" → exclude chicken thighs, chicken breast; '
        '"vegetarian" → exclude chicken thighs, chicken breast, salmon).\n\n'
        f"Known meal names and ingredients: {_KNOWN_TERMS_TEXT}\n\n"
        'Return a JSON object with "excluded_terms": a list of lowercase strings '
        "taken from the known list above. Return an empty list if nothing applies."
    )

    try:
        result = GeminiAgent().process(prompt, response_schema=_PreferenceExclusions)
        return [t.lower().strip() for t in result.excluded_terms if t.strip()]
    except Exception:
        return _fallback_exclusions(preferences)


def _fallback_exclusions(preferences: str) -> list[str]:
    """Simple 'no X' parser used when the Gemini call fails."""
    excluded = []
    for phrase in preferences.lower().split(","):
        phrase = phrase.strip()
        if phrase.startswith("no "):
            excluded.append(phrase[3:].strip())
    return excluded
