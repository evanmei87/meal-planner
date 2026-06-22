import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.llm_agent import GeminiAgent, DEFAULT_MODEL


def test_default_model():
    assert DEFAULT_MODEL == "gemini-2.5-flash-lite"


def test_gemini_agent_processes_parsed_response():
    mock_client = MagicMock()
    mock_response = MagicMock()
    from tools.food_processor import IngredientResponseSchema, IngredientItem
    mock_response.parsed = IngredientResponseSchema(
        ingredients=[IngredientItem(raw_phrase="spinach", standardized_item="Spinach", quantity=1, unit="count", corgis_style_query="Spinach, raw")]
    )
    mock_response.text = ""
    mock_client.models.generate_content.return_value = mock_response

    import tools.llm_agent as la
    original_genai = la.genai
    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client
    la.genai = mock_genai

    try:
        agent = GeminiAgent(api_key="test-key")
        result = agent.process("spinach", response_schema=IngredientResponseSchema)
        assert len(result.ingredients) == 1
        assert result.ingredients[0].standardized_item == "Spinach"
    finally:
        la.genai = original_genai


def test_gemini_agent_falls_back_to_text():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = '{"ingredients": [{"raw_phrase": "chicken", "standardized_item": "Chicken", "quantity": 1, "unit": "lbs", "corgis_style_query": "Chicken"}]}'
    mock_client.models.generate_content.return_value = mock_response

    import tools.llm_agent as la
    original_genai = la.genai
    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client
    la.genai = mock_genai

    try:
        agent = GeminiAgent(api_key="test-key")
        from tools.food_processor import IngredientResponseSchema
        result = agent.process("chicken", response_schema=IngredientResponseSchema)
        assert len(result.ingredients) == 1
        assert result.ingredients[0].standardized_item == "Chicken"
    finally:
        la.genai = original_genai


def test_gemini_agent_raises_on_empty_response():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = ""
    mock_client.models.generate_content.return_value = mock_response

    import tools.llm_agent as la
    original_genai = la.genai
    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client
    la.genai = mock_genai

    try:
        agent = GeminiAgent(api_key="test-key")
        from tools.food_processor import IngredientResponseSchema
        try:
            agent.process("nothing", response_schema=IngredientResponseSchema)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    finally:
        la.genai = original_genai
