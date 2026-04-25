from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin-metrics"])


@router.get("/metrics", dependencies=[Depends(require_admin)])
async def get_admin_metrics(request: Request) -> dict[str, object]:
    metrics = request.app.state.runtime_metrics
    return {
        "requests_total": metrics["requests_total"],
        "token_usage_total": metrics["token_usage_total"],
        "delegation_trace_count": len(metrics["delegation_traces"]),
        "latest_delegation_trace": metrics["delegation_traces"][-1] if metrics["delegation_traces"] else [],
        "latest_rag_metrics": metrics["rag_metrics_history"][-1] if metrics["rag_metrics_history"] else {},
    }
