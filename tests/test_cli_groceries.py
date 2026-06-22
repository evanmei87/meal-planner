import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from unittest.mock import patch, MagicMock
import main


@pytest.fixture
def state_path(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    monkeypatch.setattr("tools.grocery_inventory.STATE_PATH", path)
    return path


def test_groceries_add_text_parses_and_saves(state_path, monkeypatch, capsys):
    mock_items = [
        MagicMock(
            raw_phrase="2 lbs chicken",
            standardized_item="Chicken",
            quantity=2.0,
            unit="lbs",
            corgis_style_query="Chicken, broilers or fryers",
        )
    ]
    mock_meta = {
        "raw_phrase": "2 lbs chicken",
        "standardized_item": "Chicken",
        "quantity": 2.0,
        "unit": "lbs",
        "corgis_description": "Chicken",
        "confidence_score": 0.95,
        "confidence_level": "high",
        "should_auto_save": True,
        "source": "corgis",
    }
    monkeypatch.setattr("main.parse_ingredients", lambda text: mock_items)
    monkeypatch.setattr("main.get_ingredient_metadata", lambda item: mock_meta)
    monkeypatch.setattr("main.add_inventory_items", lambda items: {"added": [mock_meta], "inventory": [mock_meta]})
    monkeypatch.setattr("main.add_unmatched_items", lambda items: {"added": [], "unmatched": []})

    args = MagicMock()
    args.text = "2 lbs chicken"
    args.generate = False
    main.groceries_add_text(args)

    captured = capsys.readouterr()
    assert "2 lbs chicken" in captured.out
    assert "Chicken" in captured.out


def test_groceries_list_shows_inventory(state_path, monkeypatch, capsys):
    monkeypatch.setattr("main.format_inventory_for_cli", lambda: "## Grocery Inventory\n- Chicken: 2 lbs")
    args = MagicMock()
    main.groceries_list(args)
    captured = capsys.readouterr()
    assert "Grocery Inventory" in captured.out


def test_groceries_clear_empties_inventory(state_path, monkeypatch, capsys):
    monkeypatch.setattr("main.clear_inventory", lambda: True)
    args = MagicMock()
    main.groceries_clear(args)
    captured = capsys.readouterr()
    assert "cleared" in captured.out.lower()
