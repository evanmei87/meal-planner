import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from unittest.mock import patch
from tools.grocery_inventory import (
    add_inventory_items,
    get_inventory,
    add_unmatched_items,
    clear_inventory,
    format_inventory_for_cli,
    is_perishable,
)


@pytest.fixture
def state_path(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    monkeypatch.setattr("tools.grocery_inventory.STATE_PATH", path)
    return path


def test_add_inventory_items_new(state_path):
    items = [
        {"standardized_item": "Chicken", "quantity": 1, "unit": "lbs"},
        {"standardized_item": "Spinach", "quantity": 2, "unit": "cups"},
    ]
    result = add_inventory_items(items)
    assert len(result["added"]) == 2
    assert len(result["inventory"]) == 2
    names = {i["standardized_item"] for i in result["inventory"]}
    assert names == {"Chicken", "Spinach"}


def test_add_inventory_items_merges_duplicates(state_path):
    add_inventory_items([
        {"standardized_item": "Chicken", "quantity": 1, "unit": "lbs"},
    ])
    result = add_inventory_items([
        {"standardized_item": "Chicken", "quantity": 2, "unit": "lbs"},
    ])
    assert len(result["added"]) == 0
    assert len(result["inventory"]) == 1
    assert result["inventory"][0]["quantity"] == 3


def test_get_inventory_returns_saved_items(state_path):
    add_inventory_items([
        {"standardized_item": "Chicken", "quantity": 1, "unit": "lbs"},
    ])
    inventory = get_inventory()
    assert len(inventory) == 1
    assert inventory[0]["standardized_item"] == "Chicken"


def test_add_unmatched_items_appends(state_path):
    add_unmatched_items([
        {"raw_phrase": "mystery item", "unit": "count"},
    ])
    state = json.loads(state_path.read_text())
    assert len(state["unmatched_groceries"]) == 1
    assert state["unmatched_groceries"][0]["raw_phrase"] == "mystery item"


def test_unmatched_item_can_be_saved_as_specialty_macro(state_path):
    from tools.add_saved_meal import validate_macro_entry, append_specialty_ingredient
    valid, macros = validate_macro_entry("1 cup", "200", "20", "30", "10")
    assert valid is True
    assert macros["calories"] == 200
    content = "# Specialty Ingredients\n\n| Ingredient | Portion | Calories | Protein | Carbs | Fat |\n|:---|:---:|:---:|:---:|:---:|:---:|\n"
    success, name, updated = append_specialty_ingredient("Mystery Food", macros, content)
    assert success is True
    assert name == "Mystery Food"
    assert "Mystery Food" in updated


def test_clear_inventory_empties_state(state_path):
    add_inventory_items([
        {"standardized_item": "Chicken", "quantity": 1, "unit": "lbs"},
    ])
    add_unmatched_items([
        {"raw_phrase": "mystery item", "unit": "count"},
    ])
    success = clear_inventory()
    assert success is True
    state = json.loads(state_path.read_text())
    assert state["grocery_inventory"] == []
    assert state["unmatched_groceries"] == []
    assert state["inventory_usage"] == {"used": [], "unused": [], "supplemental": []}


def test_format_inventory_empty_message(state_path):
    msg = format_inventory_for_cli()
    assert "empty" in msg.lower()


def test_is_perishable_protein_dairy_vegetable_fruit():
    assert is_perishable({"standardized_item": "Chicken", "corgis_category": "Protein"}) is True
    assert is_perishable({"standardized_item": "Milk", "corgis_category": "Dairy"}) is True
    assert is_perishable({"standardized_item": "Spinach", "corgis_category": "Vegetable"}) is True
    assert is_perishable({"standardized_item": "Apples", "corgis_category": "Fruit"}) is True
    assert is_perishable({"standardized_item": "Rice", "corgis_category": "Grain"}) is False
