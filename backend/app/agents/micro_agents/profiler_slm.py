from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

try:
    from litellm import acompletion
except ImportError:  # pragma: no cover - optional at runtime
    acompletion = None

_PROFILER_SYSTEM_PROMPT = """
You are a conversational profiler for a financial AI assistant.
Analyze only the provided new messages and update the conversational profile.

Return strictly one JSON object with this schema:
{
  "tone": "calm|neutral|urgent|frustrated|confident|anxious",
  "financial_education_level": "beginner|intermediate|advanced|unknown",
  "frustrations": ["short phrase", "short phrase"],
  "communication_preferences": {
    "verbosity": "short|balanced|detailed",
    "style": "direct|guided|didactic"
  },
  "summary": "one short sentence",
  "confidence": 0.0
}

Rules:
- Keep existing information when new evidence is weak.
- Never include markdown or explanations outside JSON.
- Confidence must be between 0 and 1.
""".strip()

_TONE_HINTS = {
    "frustrated": ["frustrat", "angry", "upset", "annoy", "why does this fail"],
    "urgent": ["urgent", "asap", "now", "immediately"],
    "anxious": ["worried", "nervous", "scared", "uncertain"],
    "confident": ["i know", "already tried", "definitely"],
}


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if not content:
        return {}

    try:
        payload = json.loads(content)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}

    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _default_profile(current_profile: dict[str, Any]) -> dict[str, Any]:
    base_profile: dict[str, Any] = {
        "tone": "neutral",
        "financial_education_level": "unknown",
        "frustrations": [],
        "communication_preferences": {
            "verbosity": "balanced",
            "style": "guided",
        },
        "summary": "No conversational profile yet.",
        "confidence": 0.3,
    }

    if not isinstance(current_profile, dict):
        return base_profile

    merged = base_profile.copy()
    for key, value in current_profile.items():
        if key == "communication_preferences" and isinstance(value, dict):
            merged_preferences = dict(base_profile["communication_preferences"])
            merged_preferences.update(value)
            merged[key] = merged_preferences
            continue
        merged[key] = value
    return merged


def _normalize_profile(candidate: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    profile = dict(fallback)

    tone = candidate.get("tone")
    if isinstance(tone, str) and tone.strip():
        profile["tone"] = tone.strip().lower()

    level = candidate.get("financial_education_level")
    if isinstance(level, str) and level.strip():
        profile["financial_education_level"] = level.strip().lower()

    frustrations = candidate.get("frustrations")
    if isinstance(frustrations, list):
        normalized_frustrations = [
            str(item).strip() for item in frustrations if str(item).strip()
        ][:5]
        profile["frustrations"] = normalized_frustrations

    preferences = candidate.get("communication_preferences")
    if isinstance(preferences, dict):
        existing_preferences = profile.get("communication_preferences", {})
        merged_preferences = dict(existing_preferences) if isinstance(existing_preferences, dict) else {}
        merged_preferences.update(
            {
                key: str(value).strip().lower()
                for key, value in preferences.items()
                if str(value).strip()
            }
        )
        profile["communication_preferences"] = merged_preferences

    summary = candidate.get("summary")
    if isinstance(summary, str) and summary.strip():
        profile["summary"] = summary.strip()

    confidence = candidate.get("confidence")
    if isinstance(confidence, (int, float)):
        profile["confidence"] = max(0.0, min(1.0, float(confidence)))

    profile["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    return profile


def _fallback_profile_update(
    current_profile: dict[str, Any],
    new_messages: list[str],
) -> dict[str, Any]:
    profile = _default_profile(current_profile)
    joined = " ".join(message.lower() for message in new_messages)

    detected_tone = "neutral"
    for tone, hints in _TONE_HINTS.items():
        if any(hint in joined for hint in hints):
            detected_tone = tone
            break

    if any(keyword in joined for keyword in ["apy", "portfolio", "volatility", "hedge"]):
        level = "advanced"
    elif any(keyword in joined for keyword in ["interest", "budget", "debt", "savings"]):
        level = "intermediate"
    else:
        level = "beginner"

    frustrations: list[str] = []
    if "fee" in joined:
        frustrations.append("Concerned about fees")
    if "delay" in joined or "late" in joined:
        frustrations.append("Sensitive to response delays")
    if "confusing" in joined or "complex" in joined:
        frustrations.append("Needs simpler explanations")

    heuristic_profile = {
        "tone": detected_tone,
        "financial_education_level": level,
        "frustrations": frustrations,
        "communication_preferences": {
            "verbosity": "balanced",
            "style": "guided",
        },
        "summary": "Profile updated with deterministic fallback heuristics.",
        "confidence": 0.45,
    }
    return _normalize_profile(heuristic_profile, profile)


async def update_conversational_profile(
    current_profile: dict[str, Any],
    new_messages: list[str],
) -> dict[str, Any]:
    """Update conversational profile from new conversation messages.

    When the SLM is unavailable, the function falls back to deterministic heuristics.
    """

    sanitized_messages = [message.strip() for message in new_messages if message and message.strip()]
    base_profile = _default_profile(current_profile)

    if not sanitized_messages:
        return _normalize_profile({}, base_profile)

    if acompletion is None:
        return _fallback_profile_update(base_profile, sanitized_messages)

    settings = get_settings()
    user_payload = {
        "current_profile": base_profile,
        "new_messages": sanitized_messages,
    }

    try:
        response = await acompletion(
            model=settings.profiler_model,
            temperature=0,
            max_tokens=260,
            messages=[
                {"role": "system", "content": _PROFILER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
            ],
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return _fallback_profile_update(base_profile, sanitized_messages)

    content = ""
    if response and getattr(response, "choices", None):
        first_choice = response.choices[0]
        message = getattr(first_choice, "message", None)
        content = str(getattr(message, "content", "")).strip()

    candidate_profile = _extract_json(content)
    if not candidate_profile:
        return _fallback_profile_update(base_profile, sanitized_messages)

    return _normalize_profile(candidate_profile, base_profile)
