"""
backend/app/core/llm.py
========================

Wrapper LiteLLM con interfaz `acomplete(system, user, ...)` que usan los
micro-agents. Soporta `response_format={"type": "json_object"}` para forzar JSON.

El modelo concreto se elige por `role`:
    profiler    -> LITELLM_MODEL_PROFILER
    planner     -> LITELLM_MODEL_PLANNER
    responder   -> LITELLM_MODEL_RESPONDER
    guardrail   -> LITELLM_MODEL_GUARDRAIL
    summarizer  -> LITELLM_MODEL_SUMMARIZER
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class _LiteLLMClient:
    def __init__(self, model: str):
        self.model = model

    async def acomplete(
        self,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 800,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Import dentro del método para no obligar a litellm en CI minimal
        from litellm import acompletion

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs: Dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        settings = get_settings()
        if self.model.startswith(("ollama/", "ollama_chat/")):
            kwargs["api_base"] = settings.OLLAMA_API_BASE
            if response_format is not None:
                kwargs["format"] = "json"
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            resp = await acompletion(**kwargs)
            return resp["choices"][0]["message"]["content"] or ""
        except Exception as e:
            logger.exception("LiteLLM falló (model=%s): %s", self.model, str(e))
            # Return graceful fallback — JSON if response_format requested, else plain text
            if response_format and response_format.get("type") == "json_object":
                return self._mock_json_response()
            return self._mock_text_response()

    def _mock_json_response(self) -> str:
        """Fallback JSON response when LiteLLM is unavailable."""
        return """{
            "intent": "informacion_general",
            "sentiment": "neutral",
            "urgency": "low",
            "formality": "neutral",
            "topic": null,
            "mentions_money_amount": false,
            "queries": [],
            "depth": "shallow"
        }"""

    def _mock_text_response(self) -> str:
        """Fallback text response when LiteLLM is unavailable."""
        return (
            "Estoy en modo demo sin API key configurada. "
            "Para activar respuestas con IA real, "
            "agrega tu OPENAI_API_KEY en el archivo .env. "
            "Aun así, puedes explorar la interfaz y la lógica de personalización."
        )


_ROLE_TO_MODEL_KEY = {
    "profiler": "LITELLM_MODEL_PROFILER",
    "planner": "LITELLM_MODEL_PLANNER",
    "responder": "LITELLM_MODEL_RESPONDER",
    "guardrail": "LITELLM_MODEL_GUARDRAIL",
    "summarizer": "LITELLM_MODEL_SUMMARIZER",
}


def get_llm(role: str = "responder") -> _LiteLLMClient:
    settings = get_settings()
    key = _ROLE_TO_MODEL_KEY.get(role, "LITELLM_MODEL_RESPONDER")
    model = getattr(settings, key)
    return _LiteLLMClient(model=model)
