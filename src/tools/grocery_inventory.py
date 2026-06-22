import json
from pathlib import Path
from typing import Optional

STATE_PATH = Path(__file__).parent.parent / "state" / "state.json"
PERISHABLE_CATEGORIES = {"protein", "dairy", "vegetable", "fruit"}


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "current_day": "Monday",
            "plan_id": "uuid-v4-placeholder",
            "plan": [],
            "grocery_list": [],
            "missing_macros": [],
            "grocery_inventory": [],
            "unmatched_groceries": [],
            "inventory_usage": {"used": [], "unused": [], "supplemental": []},
        }
    return json.loads(STATE_PATH.read_text())


def _save_state(state: dict) -> bool:
    try:
        STATE_PATH.write_text(json.dumps(state, indent=2))
        return True
    except OSError:
        return False


def add_inventory_items(items: list[dict]) -> dict:
    state = _load_state()
    inventory = state.get("grocery_inventory", [])

    existing_keys = {(i["standardized_item"].lower(), i["unit"].lower()) for i in inventory}
    added = []
    for item in items:
        key = (item.get("standardized_item", "").lower(), item.get("unit", "").lower())
        if key in existing_keys:
            for existing in inventory:
                if existing["standardized_item"].lower() == key[0] and existing["unit"].lower() == key[1]:
                    existing["quantity"] = existing.get("quantity", 0) + item.get("quantity", 0)
                    break
        else:
            inventory.append(dict(item))
            added.append(item)
            existing_keys.add(key)

    state["grocery_inventory"] = inventory
    _save_state(state)
    return {"added": added, "inventory": inventory}


def get_inventory() -> list[dict]:
    state = _load_state()
    return state.get("grocery_inventory", [])


def add_unmatched_items(items: list[dict]) -> dict:
    state = _load_state()
    unmatched = state.get("unmatched_groceries", [])
    existing_keys = {(i["raw_phrase"].lower(), i["unit"].lower()) for i in unmatched}
    added = []
    for item in items:
        key = (item.get("raw_phrase", "").lower(), item.get("unit", "").lower())
        if key not in existing_keys:
            unmatched.append(dict(item))
            added.append(item)
            existing_keys.add(key)
    state["unmatched_groceries"] = unmatched
    _save_state(state)
    return {"added": added, "unmatched": unmatched}


def get_unmatched() -> list[dict]:
    state = _load_state()
    return state.get("unmatched_groceries", [])


def record_inventory_usage(used: list[dict], unused: list[dict], supplemental: list[dict]) -> bool:
    state = _load_state()
    state["inventory_usage"] = {
        "used": used,
        "unused": unused,
        "supplemental": supplemental,
    }
    return _save_state(state)


def clear_inventory() -> bool:
    state = _load_state()
    state["grocery_inventory"] = []
    state["unmatched_groceries"] = []
    state["inventory_usage"] = {"used": [], "unused": [], "supplemental": []}
    return _save_state(state)


def format_inventory_for_cli() -> str:
    inventory = get_inventory()
    if not inventory:
        return "Inventory is empty. Use `groceries add --text` to add items."
    lines = ["## Grocery Inventory\n"]
    for item in inventory:
        name = item.get("standardized_item", item.get("raw_phrase", "Unknown"))
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        level = item.get("confidence_level", "unknown")
        score = item.get("confidence_score", 0.0)
        source = item.get("source", "unknown")
        lines.append(f"- {name}: {qty} {unit} | confidence={score:.2f} {level} | source={source}")
    return "\n".join(lines)


def is_perishable(item: dict) -> bool:
    category = (item.get("corgis_category", "") or "").lower()
    name = (item.get("standardized_item", "") or item.get("raw_phrase", "")).lower()
    if category in PERISHABLE_CATEGORIES:
        return True
    for keyword in ["chicken", "salmon", "beef", "pork", "yogurt", "spinach", "broccoli", "berries", "milk", "egg"]:
        if keyword in name:
            return True
    return False
