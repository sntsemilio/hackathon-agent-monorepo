"""
backend/evals/run.py
=====================

Eval harness runner. Envía 50 prompts al /chat/stream y mide:
- Latencia p50/p95
- % respuestas que mencionan sugerencia correcta
- % que respeta safety rails

Genera reporte HTML con tabla resumen y radar por segmento.

Uso:
    python -m evals.run --base-url http://localhost:8080
    python -m evals.run --base-url http://localhost:8080 --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

from evals.prompts import EVAL_PROMPTS, EvalPrompt


async def run_single_prompt(
    client: Any, base_url: str, prompt: EvalPrompt
) -> Dict[str, Any]:
    """Envía un prompt al /chat/stream y recopila resultados."""
    payload = {"user_id": prompt.user_id, "message": prompt.text}
    t0 = time.monotonic()

    try:
        async with client.stream(
            "POST", f"{base_url}/chat/stream", json=payload, timeout=30.0
        ) as resp:
            final_response = ""
            events: list[Dict[str, Any]] = []
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        evt = json.loads(line[6:])
                        events.append(evt)
                        if evt.get("event") == "node_update":
                            data = evt.get("data", {})
                            if data.get("final_response"):
                                final_response = data["final_response"]
                    except json.JSONDecodeError:
                        pass

        latency_ms = (time.monotonic() - t0) * 1000
        return {
            "prompt": prompt.text,
            "user_id": prompt.user_id,
            "segment": prompt.segment_conductual,
            "intent_category": prompt.intent_category,
            "expected_suggestion": prompt.expected_suggestion,
            "safety_check": prompt.safety_check,
            "final_response": final_response,
            "latency_ms": round(latency_ms, 2),
            "events_count": len(events),
            "suggestion_hit": _check_suggestion(final_response, prompt.expected_suggestion),
            "safety_pass": _check_safety(final_response, prompt.safety_check),
        }
    except Exception as exc:
        latency_ms = (time.monotonic() - t0) * 1000
        return {
            "prompt": prompt.text,
            "user_id": prompt.user_id,
            "segment": prompt.segment_conductual,
            "error": str(exc),
            "latency_ms": round(latency_ms, 2),
            "suggestion_hit": False,
            "safety_pass": True,
        }


def _check_suggestion(response: str, expected: str | None) -> bool:
    if not expected:
        return True  # no expectation
    needle = expected.replace("_", " ").lower()
    return needle in response.lower()


def _check_safety(response: str, check: str | None) -> bool:
    if not check:
        return True
    # "NO debe ofrecer X" → check X is not in response
    parts = check.replace("NO debe ofrecer ", "").strip().lower()
    return parts not in response.lower()


def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computa métricas agregadas."""
    latencies = [r["latency_ms"] for r in results if "error" not in r]
    by_segment: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_segment[r.get("segment", "unknown")].append(r)

    segment_metrics = {}
    for seg, seg_results in by_segment.items():
        seg_lats = [r["latency_ms"] for r in seg_results if "error" not in r]
        total = len(seg_results)
        sugg_hits = sum(1 for r in seg_results if r.get("suggestion_hit"))
        safety_passes = sum(1 for r in seg_results if r.get("safety_pass"))
        segment_metrics[seg] = {
            "total": total,
            "latency_p50": round(statistics.median(seg_lats), 2) if seg_lats else 0,
            "latency_p95": round(sorted(seg_lats)[int(len(seg_lats)*0.95)] if seg_lats else 0, 2),
            "suggestion_hit_pct": round(sugg_hits / total * 100, 1) if total else 0,
            "safety_pass_pct": round(safety_passes / total * 100, 1) if total else 0,
        }

    return {
        "total_prompts": len(results),
        "errors": sum(1 for r in results if "error" in r),
        "latency_p50": round(statistics.median(latencies), 2) if latencies else 0,
        "latency_p95": round(sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0, 2),
        "suggestion_hit_pct": round(
            sum(1 for r in results if r.get("suggestion_hit")) / len(results) * 100, 1
        ) if results else 0,
        "safety_pass_pct": round(
            sum(1 for r in results if r.get("safety_pass")) / len(results) * 100, 1
        ) if results else 0,
        "by_segment": segment_metrics,
    }


def generate_html_report(metrics: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """Genera reporte HTML con tabla y radar Chart.js."""
    segments = list(metrics.get("by_segment", {}).keys())
    seg_data = metrics.get("by_segment", {})
    sugg_values = [seg_data[s]["suggestion_hit_pct"] for s in segments]
    safety_values = [seg_data[s]["safety_pass_pct"] for s in segments]
    labels_js = json.dumps(segments)
    sugg_js = json.dumps(sugg_values)
    safety_js = json.dumps(safety_values)

    rows = ""
    for r in results:
        status = "✅" if r.get("suggestion_hit") and r.get("safety_pass") else "⚠️"
        err = r.get("error", "")
        rows += f"""<tr>
            <td>{status}</td><td>{r.get('segment','')}</td>
            <td>{r.get('prompt','')[:60]}</td><td>{r.get('latency_ms',0):.0f}ms</td>
            <td>{'✓' if r.get('suggestion_hit') else '✗'}</td>
            <td>{'✓' if r.get('safety_pass') else '✗'}</td>
            <td style="color:red">{err[:40]}</td></tr>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Havi Eval Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{{font-family:Inter,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:2rem}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #333;padding:8px;text-align:left}}
th{{background:#1a1a1a}}.metric{{display:inline-block;background:#1a1a1a;border-radius:12px;
padding:1.5rem;margin:0.5rem;min-width:180px;text-align:center}}
.metric h3{{color:#00C389;margin:0}}.metric p{{font-size:2rem;margin:0.5rem 0}}
canvas{{max-width:500px;margin:2rem auto;display:block}}</style></head><body>
<h1 style="color:#00C389">🧪 Havi Eval Report</h1>
<div>
<div class="metric"><h3>Total</h3><p>{metrics['total_prompts']}</p></div>
<div class="metric"><h3>P50</h3><p>{metrics['latency_p50']}ms</p></div>
<div class="metric"><h3>P95</h3><p>{metrics['latency_p95']}ms</p></div>
<div class="metric"><h3>Sugerencia</h3><p>{metrics['suggestion_hit_pct']}%</p></div>
<div class="metric"><h3>Safety</h3><p>{metrics['safety_pass_pct']}%</p></div>
<div class="metric"><h3>Errores</h3><p>{metrics['errors']}</p></div>
</div>
<canvas id="radar" width="500" height="500"></canvas>
<script>new Chart(document.getElementById('radar'),{{type:'radar',data:{{
labels:{labels_js},datasets:[
{{label:'Sugerencia %',data:{sugg_js},borderColor:'#00C389',backgroundColor:'rgba(0,195,137,0.1)'}},
{{label:'Safety %',data:{safety_js},borderColor:'#FF6B6B',backgroundColor:'rgba(255,107,107,0.1)'}}
]}},options:{{scales:{{r:{{min:0,max:100}}}}}}}});</script>
<h2>Detalle por prompt</h2>
<table><thead><tr><th>St</th><th>Segmento</th><th>Prompt</th><th>Latencia</th>
<th>Sugerencia</th><th>Safety</th><th>Error</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""


async def main(base_url: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"DRY RUN: {len(EVAL_PROMPTS)} prompts listos contra {base_url}")
        for p in EVAL_PROMPTS:
            print(f"  [{p.segment_conductual}] {p.text[:50]}...")
        return

    if httpx is None:
        print("ERROR: httpx no instalado. pip install httpx")
        sys.exit(1)

    print(f"Running {len(EVAL_PROMPTS)} prompts against {base_url}...")
    results: list[Dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for i, prompt in enumerate(EVAL_PROMPTS):
            print(f"  [{i+1}/{len(EVAL_PROMPTS)}] {prompt.text[:40]}...", end=" ")
            result = await run_single_prompt(client, base_url, prompt)
            results.append(result)
            status = "✓" if "error" not in result else "✗"
            print(f"{status} {result['latency_ms']:.0f}ms")

    metrics = compute_metrics(results)
    report_html = generate_html_report(metrics, results)

    out_dir = Path(__file__).parent / "reports"
    out_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"eval_report_{ts}.html"
    report_path.write_text(report_html, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"Latency P50: {metrics['latency_p50']}ms | P95: {metrics['latency_p95']}ms")
    print(f"Suggestion hit: {metrics['suggestion_hit_pct']}%")
    print(f"Safety pass: {metrics['safety_pass_pct']}%")
    print(f"Errors: {metrics['errors']}/{metrics['total_prompts']}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Havi Eval Harness")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Backend URL")
    parser.add_argument("--dry-run", action="store_true", help="Only list prompts")
    args = parser.parse_args()
    asyncio.run(main(args.base_url, args.dry_run))
