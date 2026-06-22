from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

DEFAULT_MODEL = "gemini-2.5-flash-lite"


def _read_env_file_api_key() -> str | None:
    """Read GEMINI_API_KEY from a local .env file if it is not already in the environment."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return None

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "GEMINI_API_KEY":
                value = value.strip().strip('"').strip("'")
                return value or None
    except OSError:
        return None

    return None


def _resolve_api_key(api_key: str | None = None) -> str | None:
    """Resolve the Gemini API key from explicit input, environment, or .env."""
    if api_key:
        return api_key

    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    return _read_env_file_api_key()


try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without google-genai installed
    class _FallbackGenerateContentConfig:
        def __init__(self, **kwargs: Any):
            self.__dict__.update(kwargs)

    class _FallbackModels:
        def generate_content(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("google-genai is not installed")

    class _FallbackClient:
        def __init__(self, api_key: str | None = None):
            self.api_key = api_key
            self.models = _FallbackModels()

    genai = SimpleNamespace(Client=_FallbackClient)
    types = SimpleNamespace(GenerateContentConfig=_FallbackGenerateContentConfig)


class GeminiAgent:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.model = model
        self.api_key = _resolve_api_key(api_key)
        self.client = genai.Client(api_key=self.api_key)

    def process(self, prompt: str, response_schema: type[BaseModel] | None = None) -> BaseModel:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            return parsed

        text = getattr(response, "text", None)
        if text and response_schema is not None:
            return response_schema.model_validate_json(text)

        raise ValueError("No parsed response or text returned from Gemini")
