import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from unittest.mock import patch, MagicMock
from tools.generate_plan import (
    load_state,
    save_state,
    update_plan_in_state,
    _default_state,
)


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "state.json"


def _make_day_plan(ingredients):
    return {
        "day": "Monday",
        "meals": [
            {
                "name": "Test Meal",
                "calories": 500,
                "macros": {"protein": 30, "carbs": 50, "fat": 15},
                "ingredients": ingredients,
            }
        ],
        "total_calories": 500,
        "total_protein": 30,
        "total_carbs": 50,
    }


def test_generation_records_inventory_usage(state_path):
    inventory = [
        {"standardized_item": "Chicken Thighs", "quantity": 2, "unit": "lbs"},
        {"standardized_item": "White Rice", "quantity": 3, "unit": "cups"},
    ]
    day_plans = [_make_day_plan(["Chicken Thighs", "White Rice"])]
    updates = {"ate_out": False, "extra_items": [], "removed_items": []}

    state = _default_state()
    state["grocery_inventory"] = inventory

    updated = update_plan_in_state(state, day_plans, ["Monday"], updates, inventory=inventory)

    usage = updated["inventory_usage"]
    assert len(usage["used"]) == 2
    assert len(usage["unused"]) == 0
    assert len(usage["supplemental"]) == 0
    used_names = {i["standardized_item"] for i in usage["used"]}
    assert used_names == {"Chicken Thighs", "White Rice"}


def test_no_inventory_keeps_legacy_grocery_list(state_path):
    inventory = []
    day_plans = [_make_day_plan(["Chicken Thighs", "White Rice"])]
    updates = {"ate_out": False, "extra_items": [], "removed_items": []}

    state = _default_state()
    state["grocery_inventory"] = inventory

    updated = update_plan_in_state(state, day_plans, ["Monday"], updates, inventory=None)

    assert "grocery_list" in updated
    assert len(updated["grocery_list"]) > 0
    items = [i["item"] for i in updated["grocery_list"]]
    assert "Chicken Thighs" in items
    assert "White Rice" in items
