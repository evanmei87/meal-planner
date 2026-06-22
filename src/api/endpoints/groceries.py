from fastapi import APIRouter, HTTPException

from src.api.models import GroceriesRequest, GroceriesResponse, GroceryParseResult
from src.tools.food_processor import parse_ingredients, get_ingredient_metadata
from src.tools.grocery_inventory import add_inventory_items, add_unmatched_items

router = APIRouter(prefix="/groceries", tags=["Groceries"])


@router.post("/", response_model=GroceriesResponse)
async def add_groceries(request: GroceriesRequest):
    """Parse natural-language grocery text and save high-confidence items to inventory."""
    try:
        ingredients = parse_ingredients(request.text)
        items: list[GroceryParseResult] = []
        to_save: list[dict] = []
        unmatched: list[dict] = []

        for ingredient in ingredients:
            meta = get_ingredient_metadata(ingredient)
            status = _classify_status(meta)
            items.append(GroceryParseResult(
                raw_phrase=meta.get("raw_phrase", ""),
                standardized_item=meta.get("standardized_item", ""),
                quantity=float(meta.get("quantity", 0)),
                unit=meta.get("unit", ""),
                match=meta.get("corgis_description") or meta.get("source", ""),
                confidence_score=float(meta.get("confidence_score", 0.0)),
                confidence_level=meta.get("confidence_level", ""),
                status=status,
            ))
            if meta.get("should_auto_save"):
                to_save.append(meta)
            else:
                unmatched.append(meta)

        saved_count = 0
        if to_save:
            result = add_inventory_items(to_save)
            saved_count = len(result.get("added", []))

        if unmatched:
            add_unmatched_items(unmatched)

        return GroceriesResponse(items=items, saved_count=saved_count, review_count=len(unmatched))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse groceries: {str(e)}")


def _classify_status(meta: dict) -> str:
    if meta.get("should_auto_save"):
        return "auto"
    if meta.get("source") == "specialty" or not meta.get("corgis_description"):
        return "manual"
    return "review"
