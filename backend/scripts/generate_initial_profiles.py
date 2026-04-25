from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import get_settings
from app.core.database import (
    create_redis_client,
    set_conversational_profile,
    set_shared_redis_client,
)


def _mock_havi_logs() -> list[dict[str, Any]]:
    """Simulate ingestion rows from Havi conversation and behavior logs."""

    return [
        {
            "user_id": "havi-user-001",
            "tone": "neutral",
            "financial_education_level": "intermediate",
            "frustrations": ["Needs clearer investment comparisons"],
            "summary": "Frequently asks about balancing debt and savings.",
        },
        {
            "user_id": "havi-user-002",
            "tone": "frustrated",
            "financial_education_level": "beginner",
            "frustrations": ["Confused by financial jargon", "Worried about hidden fees"],
            "summary": "Prefers simple examples and direct recommendations.",
        },
        {
            "user_id": "havi-user-003",
            "tone": "confident",
            "financial_education_level": "advanced",
            "frustrations": ["Needs deeper scenario simulation"],
            "summary": "Evaluates portfolio diversification and risk-adjusted returns.",
        },
    ]


def _build_profile(log_entry: dict[str, Any]) -> dict[str, Any]:
    """Transform a simulated log entry into a conversational profile payload."""

    return {
        "tone": str(log_entry.get("tone", "neutral")),
        "financial_education_level": str(log_entry.get("financial_education_level", "unknown")),
        "frustrations": [
            str(item)
            for item in log_entry.get("frustrations", [])
            if str(item).strip()
        ],
        "communication_preferences": {
            "verbosity": "balanced",
            "style": "guided",
        },
        "summary": str(log_entry.get("summary", "Initial profile generated from logs.")),
        "confidence": 0.7,
        "origin": "havi_log_bootstrap",
        "last_updated_utc": datetime.now(timezone.utc).isoformat(),
    }


async def _seed_profiles(log_rows: list[dict[str, Any]]) -> int:
    """Persist all generated profiles concurrently in Redis."""

    tasks = []
    for row in log_rows:
        user_id = str(row.get("user_id", "")).strip()
        if not user_id:
            continue
        tasks.append(
            set_conversational_profile(
                user_id=user_id,
                profile_data=_build_profile(row),
            )
        )

    if not tasks:
        return 0

    await asyncio.gather(*tasks)
    return len(tasks)


async def main() -> None:
    """Entry point for generating initial conversational profiles."""

    settings = get_settings()
    redis_client = create_redis_client(settings)
    set_shared_redis_client(redis_client)

    try:
        inserted = await _seed_profiles(_mock_havi_logs())
        print(
            json.dumps(
                {
                    "status": "ok",
                    "source": "havi_simulated_logs",
                    "profiles_seeded": inserted,
                },
                ensure_ascii=True,
            )
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "detail": str(exc)}, ensure_ascii=True))
        raise
    finally:
        set_shared_redis_client(None)
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
