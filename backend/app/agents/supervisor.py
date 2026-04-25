from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from app.agents.micro_agents.guardrail_slm import guardrail_node
from app.agents.state import GlobalState
from app.agents.teams.research.graph import build_research_subgraph
from app.agents.teams.tool_ops.graph import build_tool_ops_subgraph
from app.core.config import get_settings

try:
    from litellm import acompletion
except ImportError:  # pragma: no cover - optional at runtime
    acompletion = None


class SupervisorState(GlobalState, total=False):
    next_team: Literal["research", "tool_ops", "END"]
    delegation_trace: list[str]
    final_response: str


_TOOL_KEYWORDS = {
    "tool",
    "execute",
    "run",
    "python",
    "code",
    "calculate",
    "compute",
}

_ROUTER_SYSTEM_PROMPT = """
You are the routing supervisor for a financial assistant.
Decide if the request should go to RESEARCH or TOOL_OPS.

Decision policy:
- Read user_persona.analytics_insights.salud_financiera before deciding.
- Read user_persona.conversational_profile (tone, education level, frustrations).
- Prefer RESEARCH when the user needs conceptual explanation, guidance, or trust-building.
- Prefer TOOL_OPS when the user explicitly asks for executable operations,
  calculations, or code execution.

Output one token only: RESEARCH or TOOL_OPS.
""".strip()

_RESEARCH_GRAPH = build_research_subgraph()
_TOOL_OPS_GRAPH = build_tool_ops_subgraph()


def _message_to_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def _latest_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return _message_to_text(message)
    if messages:
        return _message_to_text(messages[-1])
    return ""


def _extract_last_ai_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = _message_to_text(message).strip()
            if text:
                return text
    if messages:
        return _message_to_text(messages[-1]).strip()
    return ""


def _safe_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _persona_snapshot(state: SupervisorState) -> dict[str, Any]:
    persona = state.get("user_persona", {})
    return persona if isinstance(persona, dict) else {}


def _pick_team(state: SupervisorState, user_text: str) -> Literal["research", "tool_ops"]:
    persona = _persona_snapshot(state)
    insights = persona.get("analytics_insights", {})
    profile = persona.get("conversational_profile", {})

    score: int | None = None
    if isinstance(insights, dict):
        financial_health = insights.get("salud_financiera", {})
        if isinstance(financial_health, dict):
            score = _safe_int(financial_health.get("score"))

    tone = ""
    if isinstance(profile, dict):
        tone = str(profile.get("tone", "")).lower()

    if score is not None and score < 55:
        return "research"
    if tone in {"frustrated", "anxious"}:
        return "research"

    if state.get("base64_images"):
        return "research"
    lowered = user_text.lower()
    if any(keyword in lowered for keyword in _TOOL_KEYWORDS):
        return "tool_ops"
    return "research"


async def _pick_team_with_router_slm(
    state: SupervisorState,
    user_text: str,
) -> tuple[Literal["research", "tool_ops"] | None, str]:
    if acompletion is None:
        return None, "slm_unavailable"

    settings = get_settings()
    payload = {
        "user_text": user_text,
        "has_images": bool(state.get("base64_images")),
        "user_persona": _persona_snapshot(state),
    }

    try:
        response = await acompletion(
            model=settings.supervisor_router_model,
            temperature=0,
            max_tokens=6,
            messages=[
                {"role": "system", "content": _ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
            ],
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return None, "slm_error"

    content = ""
    if response and getattr(response, "choices", None):
        first_choice = response.choices[0]
        message = getattr(first_choice, "message", None)
        content = str(getattr(message, "content", "")).strip().upper()

    if content.startswith("TOOL_OPS"):
        return "tool_ops", "slm_decision"
    if content.startswith("RESEARCH"):
        return "research", "slm_decision"
    return None, "slm_unparsed"


async def route_request(state: SupervisorState) -> dict[str, Any]:
    current_iterations = state.get("global_iterations", 0) + 1
    trace = list(state.get("delegation_trace", []))

    if state.get("blocked"):
        trace.append("guardrail:block")
        return {
            "global_iterations": current_iterations,
            "active_team": "END",
            "next_team": "END",
            "delegation_trace": trace,
        }

    if current_iterations > 5:
        trace.append("router:fallback:max_iterations")
        return {
            "global_iterations": current_iterations,
            "final_response": "Global iteration budget reached. Returning best effort answer.",
            "active_team": "END",
            "next_team": "END",
            "delegation_trace": trace,
        }

    user_text = _latest_user_text(state.get("messages", []))
    slm_team, slm_reason = await _pick_team_with_router_slm(state, user_text)
    if slm_team is not None:
        selected_team = slm_team
        trace.append(f"router:slm:{slm_reason}->{selected_team}")
    else:
        selected_team = _pick_team(state, user_text)
        trace.append(f"router:heuristic:{slm_reason}->{selected_team}")

    return {
        "next_team": selected_team,
        "active_team": selected_team,
        "global_iterations": current_iterations,
        "delegation_trace": trace,
    }


async def call_research_team(state: SupervisorState) -> dict[str, Any]:
    subgraph_input = {
        "messages": state.get("messages", []),
        "thread_id": state.get("thread_id", ""),
        "team_iterations": 0,
        "base64_images": state.get("base64_images", []),
    }
    result = await _RESEARCH_GRAPH.ainvoke(subgraph_input)
    draft = result.get("draft", {})
    answer = draft.get("answer") if isinstance(draft, dict) else ""
    answer = answer or _extract_last_ai_text(result.get("messages", []))
    answer = answer or "Research team completed with no draft output."

    trace = list(state.get("delegation_trace", []))
    trace.append("research:complete")
    return {
        "messages": [AIMessage(content=answer)],
        "delegation_trace": trace,
        "rag_metrics": result.get("rag_metrics", {}),
        "active_team": "END",
        "final_response": answer,
    }


async def call_tool_ops_team(state: SupervisorState) -> dict[str, Any]:
    subgraph_input = {
        "messages": state.get("messages", []),
        "thread_id": state.get("thread_id", ""),
        "team_iterations": 0,
    }
    result = await _TOOL_OPS_GRAPH.ainvoke(subgraph_input)
    answer = _extract_last_ai_text(result.get("messages", []))
    answer = answer or "Tool ops team completed with no output."

    trace = list(state.get("delegation_trace", []))
    trace.append("tool_ops:complete")
    return {
        "messages": [AIMessage(content=answer)],
        "delegation_trace": trace,
        "active_team": "END",
        "final_response": answer,
    }


async def finalize_response(state: SupervisorState) -> dict[str, Any]:
    final_response = state.get("final_response")
    if not final_response:
        final_response = _extract_last_ai_text(state.get("messages", []))
    if not final_response:
        final_response = "No response generated by supervisor."
    return {"final_response": final_response, "active_team": "END"}


def _route_after_router(state: SupervisorState) -> str:
    if state.get("next_team") == "END":
        return "finalize"
    if state.get("final_response"):
        return "finalize"
    return state.get("next_team", "research")


def build_supervisor_graph(checkpointer: Any | None = None):
    workflow = StateGraph(SupervisorState)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("router", route_request)
    workflow.add_node("research", call_research_team)
    workflow.add_node("tool_ops", call_tool_ops_team)
    workflow.add_node("finalize", finalize_response)

    workflow.add_edge(START, "guardrail")
    workflow.add_edge("guardrail", "router")
    workflow.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "research": "research",
            "tool_ops": "tool_ops",
            "finalize": "finalize",
        },
    )
    workflow.add_edge("research", "finalize")
    workflow.add_edge("tool_ops", "finalize")
    workflow.add_edge("finalize", END)

    compile_kwargs: dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    return workflow.compile(**compile_kwargs)
