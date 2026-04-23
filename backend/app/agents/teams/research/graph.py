from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.teams.research.agents import (
    draft_research_response,
    gather_context,
    plan_research,
)
from app.agents.teams.research.state import ResearchState


def build_research_subgraph():
    workflow = StateGraph(ResearchState)
    workflow.add_node("research_plan", plan_research)
    workflow.add_node("research_retrieve", gather_context)
    workflow.add_node("research_draft", draft_research_response)

    workflow.add_edge(START, "research_plan")
    workflow.add_edge("research_plan", "research_retrieve")
    workflow.add_edge("research_retrieve", "research_draft")
    workflow.add_edge("research_draft", END)

    return workflow.compile()
