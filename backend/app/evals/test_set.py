from __future__ import annotations

from pydantic import BaseModel


class EvalSample(BaseModel):
    question: str
    context: list[str]
    ground_truth: str


DEFAULT_TEST_SET: list[EvalSample] = [
    EvalSample(
        question="What does hybrid retrieval combine in this platform?",
        context=[
            "Hybrid retrieval combines dense vectors with BM25 lexical scoring.",
            "Results are reranked with a cross encoder from top 15 to top 3.",
        ],
        ground_truth="Hybrid retrieval combines dense vector search and BM25, then reranks results.",
    ),
    EvalSample(
        question="How does the guardrail micro-agent react to jailbreak prompts?",
        context=[
            "Guardrail SLM runs before the supervisor routing node.",
            "If prompt injection or jailbreak attempts are detected, requests are blocked.",
        ],
        ground_truth="The guardrail blocks jailbreak attempts before delegation and returns a violation message.",
    ),
]
