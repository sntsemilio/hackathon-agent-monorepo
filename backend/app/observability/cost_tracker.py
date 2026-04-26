"""
backend/app/observability/cost_tracker.py
==========================================

Tracker de costo por sesión/modelo. Acumula tokens in/out y calcula costo
estimado USD basado en tabla de precios configurable.

Se integra con core/llm.py vía callback post-completion.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# Precios por 1K tokens (input / output) — valores aproximados Anthropic/OpenAI
DEFAULT_PRICING: Dict[str, tuple[float, float]] = {
    # (input_cost_per_1k, output_cost_per_1k)
    "anthropic/claude-haiku-4-5": (0.0008, 0.004),
    "anthropic/claude-sonnet-4-6": (0.003, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.005, 0.015),
}


@dataclass
class LLMCallRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    node: str
    timestamp: float = field(default_factory=time.time)


class LLMCostTracker:
    """Singleton que acumula costos LLM por sesión."""

    def __init__(
        self,
        pricing: Dict[str, tuple[float, float]] | None = None,
        fallback_input_cost: float = 0.001,
        fallback_output_cost: float = 0.003,
    ) -> None:
        self._pricing = pricing or DEFAULT_PRICING
        self._fallback_input = fallback_input_cost
        self._fallback_output = fallback_output_cost
        self._sessions: Dict[str, List[LLMCallRecord]] = {}

    def record_call(
        self,
        session_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        node: str = "",
    ) -> LLMCallRecord:
        in_cost, out_cost = self._pricing.get(
            model, (self._fallback_input, self._fallback_output)
        )
        cost = (input_tokens / 1000 * in_cost) + (output_tokens / 1000 * out_cost)

        record = LLMCallRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost, 6),
            node=node,
        )
        self._sessions.setdefault(session_id, []).append(record)
        logger.debug(
            "LLM cost: session=%s model=%s tokens=%d/%d cost=$%.6f",
            session_id, model, input_tokens, output_tokens, cost,
        )
        return record

    def get_session_cost(self, session_id: str) -> Dict[str, Any]:
        records = self._sessions.get(session_id, [])
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cost = sum(r.cost_usd for r in records)
        return {
            "session_id": session_id,
            "calls": len(records),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "estimated_cost_usd": round(total_cost, 6),
            "breakdown": [
                {
                    "model": r.model,
                    "node": r.node,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "cost_usd": r.cost_usd,
                }
                for r in records
            ],
        }

    def get_all_sessions_summary(self) -> Dict[str, Any]:
        total_cost = 0.0
        total_calls = 0
        for records in self._sessions.values():
            total_calls += len(records)
            total_cost += sum(r.cost_usd for r in records)
        return {
            "total_sessions": len(self._sessions),
            "total_calls": total_calls,
            "total_cost_usd": round(total_cost, 6),
        }


# Singleton global
_tracker: LLMCostTracker | None = None


def get_cost_tracker() -> LLMCostTracker:
    global _tracker
    if _tracker is None:
        _tracker = LLMCostTracker()
    return _tracker
