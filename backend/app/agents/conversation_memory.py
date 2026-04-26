"""
Conversation memory management — load/save chat history from Redis.
"""
from typing import Any, Dict, List


async def load_conversation_history(redis_client: Any, user_id: str) -> List[Dict[str, Any]]:
    """Load conversation history for a user from Redis."""
    if not redis_client or not user_id:
        return []
    try:
        key = f"conv_history:{user_id}"
        data = await redis_client.get(key)
        if data:
            import json
            return json.loads(data)
    except Exception:
        pass
    return []


MAX_HISTORY_TURNS = 5   # keep last 5 user+assistant pairs (10 messages)


async def save_conversation_turn(
    redis_client: Any, user_id: str, user_message: str, assistant_response: str
) -> None:
    """Save a conversation turn to Redis, keeping only the last MAX_HISTORY_TURNS turns."""
    if not redis_client or not user_id:
        return
    try:
        import json
        key = f"conv_history:{user_id}"
        history = await load_conversation_history(redis_client, user_id)
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_response})
        # Trim to the last MAX_HISTORY_TURNS * 2 messages so Redis stays small
        history = history[-(MAX_HISTORY_TURNS * 2):]
        await redis_client.set(key, json.dumps(history), ex=86400)
    except Exception:
        pass


def format_history_for_prompt(history: List[Dict[str, Any]]) -> str:
    """Format conversation history for inclusion in agent prompts."""
    if not history:
        return ""
    lines = []
    for msg in history[-(MAX_HISTORY_TURNS * 2):]:
        role = "Usuario" if msg.get("role") == "user" else "Havi"
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)
