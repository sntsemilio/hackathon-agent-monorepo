from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin-evals"])


@router.get("/evals/ragas", dependencies=[Depends(require_admin)])
async def get_latest_ragas_scores(request: Request) -> dict[str, object]:
    return request.app.state.evals_runner.latest_results()


@router.post("/evals/ragas/run", dependencies=[Depends(require_admin)])
async def run_ragas_scores(request: Request) -> dict[str, object]:
    return await request.app.state.evals_runner.run()
