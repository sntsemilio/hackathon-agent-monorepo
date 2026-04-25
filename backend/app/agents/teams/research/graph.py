from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.teams.research.agents import (
    draft_research_response,
    gather_context,
    plan_research,
)
from app.agents.teams.research.state import ResearchState
from app.agents.teams.research.vision_agent import process_base64_images


async def run_vision(state: ResearchState) -> dict[str, list[str]]:
    images = state.get("base64_images", [])
    if not images:
        return {"vision_notes": []}

    summaries = await process_base64_images(images)
    notes = [
        f"image_index={item['image_index']} status={item['status']} bytes={item['bytes']}"
        for item in summaries
    ]
    return {"vision_notes": notes}


def _after_plan(state: ResearchState) -> str:
    plan = state.get("plan", {})
    if isinstance(plan, dict) and plan.get("requires_vision"):
        return "research_vision"
    return "research_retrieve"


def build_research_subgraph():
    workflow = StateGraph(ResearchState)
    workflow.add_node("research_plan", plan_research)
    workflow.add_node("research_vision", run_vision)
    workflow.add_node("research_retrieve", gather_context)
    workflow.add_node("research_draft", draft_research_response)

    workflow.add_edge(START, "research_plan")
    workflow.add_conditional_edges(
        "research_plan",
        _after_plan,
        {
            "research_vision": "research_vision",
            "research_retrieve": "research_retrieve",
        },
    )
    workflow.add_edge("research_vision", "research_retrieve")
    workflow.add_edge("research_retrieve", "research_draft")
    workflow.add_edge("research_draft", END)

    return workflow.compile()
