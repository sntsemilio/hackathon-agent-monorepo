from __future__ import annotations

from collections.abc import Sequence

from app.core.config import get_settings

try:
    from litellm import acompletion
except ImportError:  # pragma: no cover - optional at runtime
    acompletion = None


async def summarize_with_slm(
    query: str,
    evidence: Sequence[str],
    vision_notes: Sequence[str] | None = None,
) -> str:
    """Summarize evidence with a small model, with deterministic fallback."""

    context_lines = [f"- {item}" for item in evidence[:8]]
    if vision_notes:
        context_lines.extend(f"- [vision] {item}" for item in vision_notes[:4])

    prompt = (
        "Produce a concise answer using only the context below. "
        "If context is insufficient, explicitly say what is missing.\n\n"
        f"Question: {query}\n"
        f"Context:\n{'\n'.join(context_lines) if context_lines else '- no context'}"
    )

    if acompletion is None:
        return (
            f"Question: {query}\n"
            "Answer Summary:\n"
            f"{'; '.join(evidence[:3]) if evidence else 'No evidence available.'}"
        )

    settings = get_settings()
    try:
        response = await acompletion(
            model=settings.summarizer_model,
            temperature=settings.litellm_temperature,
            max_tokens=220,
            messages=[
                {
                    "role": "system",
                    "content": "You are a terse research summarizer for enterprise incident rooms.",
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception:
        return (
            f"Question: {query}\n"
            "Answer Summary:\n"
            f"{'; '.join(evidence[:3]) if evidence else 'No evidence available.'}"
        )

    if response and getattr(response, "choices", None):
        first_choice = response.choices[0]
        content = str(getattr(getattr(first_choice, "message", None), "content", "")).strip()
        if content:
            return content

    return (
        f"Question: {query}\n"
        "Answer Summary:\n"
        f"{'; '.join(evidence[:3]) if evidence else 'No evidence available.'}"
    )
