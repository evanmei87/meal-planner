import csv
import json
import os
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional

from pydantic import BaseModel, Field

from .confidence import classify_confidence, format_confidence, HIGH_CONFIDENCE_THRESHOLD, REVIEW_CONFIDENCE_THRESHOLD


PHRASE_CACHE_PATH = Path(__file__).parent.parent / "state" / "phrase_cache.json"
MATCH_ALGORITHM_VERSION = 2


class IngredientItem(BaseModel):
    raw_phrase: str
    standardized_item: str
    quantity: float
    unit: str
    corgis_style_query: str


class IngredientResponseSchema(BaseModel):
    ingredients: list[IngredientItem]


SYSTEM_PROMPT = """You are a culinary ingredient parser. Extract every ingredient from the user's grocery description.
Return a JSON object matching this schema:
{
  "ingredients": [
    {
      "raw_phrase": "original phrase from the user",
      "standardized_item": "noun describing the food item",
      "quantity": numeric_quantity,
      "unit": "normalized unit from [lb/lbs, cup/cups, count/whole, tbsp, oz, scoop/scoops]",
      "corgis_style_query": "description category-style query (e.g., 'Chicken, broilers or fryers, breast, meat only, cooked, roasted' or 'Quinoa, cooked')"
    }
  ]
}
Rules:
- Quantities must be floats.
- Units must be one of: lb/lbs, cup/cups, count/whole, tbsp, oz, scoop/scoops.
- If unit is ambiguous, default to count/whole.
- Do NOT convert volume to weight.
- corgis_style_query should be a concise noun phrase suitable for searching the USDA FoodData Central database.
- Preserve every distinct ingredient even if it appears in a compound phrase.
- If no ingredients are found, return empty ingredients array."""


def _load_food_db() -> list[dict]:
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "food.csv"
    if not csv_path.exists():
        return []
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


_FOOD_DB: list[dict] | None = None


def get_food_db() -> list[dict]:
    global _FOOD_DB
    if _FOOD_DB is None:
        _FOOD_DB = _load_food_db()
    return _FOOD_DB


def _load_phrase_cache() -> dict:
    if not PHRASE_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(PHRASE_CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_phrase_cache(cache: dict) -> None:
    try:
        PHRASE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PHRASE_CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except OSError:
        pass


def _normalize_unit(unit: str) -> str:
    u = unit.lower().strip().rstrip("s")
    mapping = {
        "lb": "lbs",
        "pound": "lbs",
        "cup": "cups",
        "count": "count",
        "whole": "count",
        "tbsp": "tbsp",
        "oz": "oz",
        "scoop": "scoops",
    }
    return mapping.get(u, "count")


def _normalize_plural_unit(unit: str) -> str:
    u = unit.lower().strip().rstrip("s")
    mapping = {
        "lb": "lbs",
        "pound": "lbs",
        "cup": "cups",
        "count": "count",
        "whole": "count",
        "tbsp": "tbsp",
        "oz": "oz",
        "scoop": "scoops",
    }
    mapped = mapping.get(u)
    if mapped is None:
        return unit.lower().strip()
    return mapped


def _normalize_food_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"\bnon[\s-]?fat\b", "nonfat", normalized)
    normalized = re.sub(r"\bskinless\b", "skin not eaten", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _canonical_food_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _food_tokens(text: str) -> set[str]:
    return {_canonical_food_token(token) for token in _normalize_food_text(text).split()}


def _strip_grocery_noise(text: str) -> str:
    stopwords = {
        "a",
        "an",
        "and",
        "bought",
        "cup",
        "cups",
        "got",
        "i",
        "lb",
        "lbs",
        "of",
        "ounce",
        "ounces",
        "oz",
        "pound",
        "pounds",
        "tub",
        "the",
    }
    tokens = []
    for token in _normalize_food_text(text).split():
        if token in stopwords:
            continue
        try:
            float(token)
            continue
        except ValueError:
            pass
        tokens.append(token)
    return " ".join(tokens)


def _build_match_query(raw_phrase: str, standardized_item: str) -> str:
    raw_query = _strip_grocery_noise(raw_phrase)
    standard_query = _strip_grocery_noise(standardized_item)
    if raw_query and standard_query:
        standard_tokens = _food_tokens(standard_query)
        extra_tokens = [
            token
            for token in raw_query.split()
            if _canonical_food_token(token) not in standard_tokens
        ]
        return " ".join([standard_query, *extra_tokens]).strip()
    return standard_query or raw_query


def _confidence_score(raw: str, candidate: str) -> float:
    r = _normalize_food_text(raw)
    c = _normalize_food_text(candidate)
    if r == c:
        return 1.0
    if c in r or r in c:
        return 0.9

    sequence_score = SequenceMatcher(None, r, c).ratio()
    raw_tokens = _food_tokens(r)
    candidate_tokens = _food_tokens(c)
    if not raw_tokens or not candidate_tokens:
        return sequence_score

    if raw_tokens.issubset(candidate_tokens):
        return 0.85 + (0.1 * (len(raw_tokens) / len(candidate_tokens)))

    overlap = raw_tokens & candidate_tokens
    if not overlap:
        return min(sequence_score, 0.35)

    query_coverage = len(overlap) / len(raw_tokens)
    candidate_precision = len(overlap) / len(candidate_tokens)
    token_score = (query_coverage * 0.75) + (candidate_precision * 0.25)
    return max(sequence_score * 0.55 + token_score * 0.45, token_score)


def _rank_food_matches(standardized_item: str, min_score: float = 0.2) -> list[dict]:
    db = get_food_db()
    if not db:
        return []
    query = standardized_item.lower().strip()
    ranked: list[dict] = []
    for row in db:
        desc = row.get("Description", "").lower()
        score = _confidence_score(query, desc)
        if score < min_score:
            continue
        result = classify_confidence(score)
        ranked.append({
            "standardized_item": standardized_item,
            "corgis_description": row.get("Description", ""),
            "corgis_category": row.get("Category", ""),
            "nutrient_data_bank_number": row.get("Nutrient Data Bank Number", ""),
            "confidence_score": result.score,
            "confidence_level": result.level,
            "should_auto_save": result.should_auto_save,
            "source": "corgis",
        })

    ranked.sort(key=lambda item: item["confidence_score"], reverse=True)
    return ranked


def get_food_match_candidates(raw_phrase: str, standardized_item: str, limit: int = 3, min_score: float = 0.2) -> list[dict]:
    query = _build_match_query(raw_phrase, standardized_item)
    candidates = _rank_food_matches(query, min_score=min_score)
    if not candidates and query != standardized_item:
        candidates = _rank_food_matches(standardized_item, min_score=min_score)
    for candidate in candidates:
        candidate["raw_phrase"] = raw_phrase
        candidate["standardized_item"] = standardized_item
    return candidates[:limit]


def match_food_item(raw_phrase: str, standardized_item: str) -> dict | None:
    candidates = get_food_match_candidates(raw_phrase, standardized_item, limit=1)
    if not candidates:
        return None
    return candidates[0]


def parse_ingredients(text: str) -> list[IngredientItem]:
    from .llm_agent import GeminiAgent
    agent = GeminiAgent()
    parsed = agent.process(SYSTEM_PROMPT + "\n\nUser input: " + text, response_schema=IngredientResponseSchema)
    return parsed.ingredients


def get_ingredient_metadata(item: IngredientItem) -> dict:
    cache = _load_phrase_cache()
    key = item.raw_phrase.lower().strip()
    if key in cache and cache[key].get("match_algorithm_version") == MATCH_ALGORITHM_VERSION:
        cached = cache[key]
        result = classify_confidence(cached.get("confidence_score", 0.0))
        out = {
            "raw_phrase": item.raw_phrase,
            "standardized_item": item.standardized_item,
            "quantity": item.quantity,
            "unit": _normalize_plural_unit(item.unit),
            "corgis_style_query": item.corgis_style_query,
            "confidence_score": result.score,
            "confidence_level": result.level,
            "should_auto_save": result.should_auto_save,
        }
        if cached.get("source") == "corgis":
            out.update({
                "corgis_description": cached.get("corgis_description", ""),
                "corgis_category": cached.get("corgis_category", ""),
                "nutrient_data_bank_number": cached.get("nutrient_data_bank_number", ""),
                "source": "corgis",
            })
        else:
            out["source"] = "specialty"
        return out

    match = match_food_item(item.raw_phrase, item.standardized_item)
    cache_entry = {
        "raw_phrase": item.raw_phrase,
        "standardized_item": item.standardized_item,
        "unit": _normalize_plural_unit(item.unit),
        "corgis_style_query": item.corgis_style_query,
        "match_algorithm_version": MATCH_ALGORITHM_VERSION,
    }
    if match:
        cache_entry.update({
            "corgis_description": match["corgis_description"],
            "corgis_category": match["corgis_category"],
            "nutrient_data_bank_number": match["nutrient_data_bank_number"],
            "confidence_score": match["confidence_score"],
            "confidence_level": match["confidence_level"],
            "should_auto_save": match["should_auto_save"],
            "source": "corgis",
        })
    else:
        cache_entry.update({
            "confidence_score": 0.0,
            "confidence_level": "low",
            "should_auto_save": False,
            "source": "specialty",
        })
    cache[key] = cache_entry
    _save_phrase_cache(cache)
    result = classify_confidence(cache_entry["confidence_score"])
    return {
        "raw_phrase": item.raw_phrase,
        "standardized_item": item.standardized_item,
        "quantity": item.quantity,
        "unit": _normalize_plural_unit(item.unit),
        "corgis_style_query": item.corgis_style_query,
        "corgis_description": cache_entry.get("corgis_description", ""),
        "corgis_category": cache_entry.get("corgis_category", ""),
        "nutrient_data_bank_number": cache_entry.get("nutrient_data_bank_number", ""),
        "confidence_score": result.score,
        "confidence_level": result.level,
        "should_auto_save": result.should_auto_save,
        "source": cache_entry["source"],
    }


def get_phrase_cache_path() -> str:
    return str(PHRASE_CACHE_PATH)
