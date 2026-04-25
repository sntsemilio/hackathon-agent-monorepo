from __future__ import annotations

import asyncio
from collections.abc import Sequence
from statistics import mean
from typing import Any

from app.evals.test_set import DEFAULT_TEST_SET, EvalSample

try:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, faithfulness
    from datasets import Dataset
except ImportError:  # pragma: no cover - optional dependency runtime
    evaluate = None
    answer_relevancy = None
    context_precision = None
    faithfulness = None
    Dataset = None


class RagasEvaluationRunner:
    def __init__(self) -> None:
        self._latest: dict[str, Any] = {
            "status": "not_run",
            "scores": {},
            "samples": len(DEFAULT_TEST_SET),
        }

    async def run(self, samples: Sequence[EvalSample] | None = None) -> dict[str, Any]:
        eval_samples = list(samples or DEFAULT_TEST_SET)

        if evaluate is None or Dataset is None:
            scores = self._fallback_scores(eval_samples)
            self._latest = {
                "status": "fallback",
                "scores": scores,
                "samples": len(eval_samples),
            }
            return self._latest

        payload = {
            "question": [item.question for item in eval_samples],
            "answer": [item.ground_truth for item in eval_samples],
            "contexts": [item.context for item in eval_samples],
            "ground_truth": [item.ground_truth for item in eval_samples],
        }
        dataset = Dataset.from_dict(payload)

        result = await asyncio.to_thread(
            evaluate,
            dataset,
            metrics=[answer_relevancy, context_precision, faithfulness],
        )
        scores = {str(key): float(value) for key, value in result.items()}
        self._latest = {
            "status": "ragas",
            "scores": scores,
            "samples": len(eval_samples),
        }
        return self._latest

    def latest_results(self) -> dict[str, Any]:
        return self._latest

    def _fallback_scores(self, eval_samples: Sequence[EvalSample]) -> dict[str, float]:
        overlaps: list[float] = []
        for sample in eval_samples:
            truth_tokens = set(sample.ground_truth.lower().split())
            context_tokens = set(" ".join(sample.context).lower().split())
            if not truth_tokens:
                overlaps.append(0.0)
                continue
            overlaps.append(len(truth_tokens & context_tokens) / len(truth_tokens))

        value = round(mean(overlaps), 4) if overlaps else 0.0
        return {
            "answer_relevancy": value,
            "context_precision": value,
            "faithfulness": value,
        }


async def run_default_ragas() -> dict[str, Any]:
    runner = RagasEvaluationRunner()
    return await runner.run()


if __name__ == "__main__":
    result = asyncio.run(run_default_ragas())
    print(result)
