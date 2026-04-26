"""
backend/app/observability/tracer.py
====================================

OpenTelemetry setup + decorator para instrumentar nodos LangGraph.

Cada nodo queda envuelto en un span OTel y emite un `NodeTraceEvent`
que routes.py serializa como SSE ``event: trace_update``.
"""
from __future__ import annotations

import functools
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Trace event dataclass (viaja vía SSE al frontend)
# ---------------------------------------------------------------------------

@dataclass
class NodeTraceEvent:
    """Representación ligera de la ejecución de un nodo."""
    node: str
    status: str = "running"          # running | done | error
    latency_ms: float = 0.0
    explanation: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# In-memory trace collector (por sesión)
# ---------------------------------------------------------------------------

class TraceCollector:
    """Acumula NodeTraceEvents por sesión para el trace panel."""

    def __init__(self) -> None:
        self._traces: Dict[str, List[NodeTraceEvent]] = {}

    def start_node(self, session_id: str, node: str, explanation: str = "") -> NodeTraceEvent:
        evt = NodeTraceEvent(node=node, status="running", explanation=explanation)
        self._traces.setdefault(session_id, []).append(evt)
        return evt

    def finish_node(
        self, session_id: str, node: str, latency_ms: float, explanation: str = ""
    ) -> NodeTraceEvent:
        evt = NodeTraceEvent(
            node=node, status="done", latency_ms=round(latency_ms, 2), explanation=explanation
        )
        traces = self._traces.setdefault(session_id, [])
        # Replace running event if exists
        for i, t in enumerate(traces):
            if t.node == node and t.status == "running":
                traces[i] = evt
                return evt
        traces.append(evt)
        return evt

    def error_node(self, session_id: str, node: str, error: str) -> NodeTraceEvent:
        evt = NodeTraceEvent(node=node, status="error", explanation=error)
        self._traces.setdefault(session_id, []).append(evt)
        return evt

    def get_traces(self, session_id: str) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._traces.get(session_id, [])]

    def clear(self, session_id: str) -> None:
        self._traces.pop(session_id, None)


# Singleton global
_collector = TraceCollector()


def get_trace_collector() -> TraceCollector:
    return _collector


# ---------------------------------------------------------------------------
# OTel setup
# ---------------------------------------------------------------------------

_tracer_provider = None


def setup_telemetry(
    service_name: str = "havi-backend",
    otlp_endpoint: str = "",
    otlp_headers: str = "",
) -> None:
    """Inicializa OpenTelemetry TracerProvider."""
    global _tracer_provider
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                headers_dict = {}
                if otlp_headers:
                    for pair in otlp_headers.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            headers_dict[k.strip()] = v.strip()
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers_dict)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info("OTLP exporter configurado: %s", otlp_endpoint)
            except Exception:
                logger.warning("OTLP exporter no disponible, usando ConsoleSpanExporter")
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            # Console fallback silencioso en demo
            logger.info("OTel: sin endpoint OTLP, traces solo en memoria")

        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        logger.info("OpenTelemetry inicializado: %s", service_name)

    except ImportError:
        logger.warning(
            "opentelemetry SDK no instalado — observability degradada a logging puro"
        )


def get_tracer(name: str = "havi") -> Any:
    """Retorna un tracer OTel si está disponible, o un stub."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _StubTracer()


class _StubTracer:
    """Stub cuando OTel no está instalado."""
    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        import contextlib
        return contextlib.nullcontext()


# ---------------------------------------------------------------------------
# Node tracing decorator
# ---------------------------------------------------------------------------

def trace_node(
    node_name: str,
    explanation_fn: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorator que envuelve un nodo LangGraph async para:
    1. Crear un span OTel
    2. Medir latencia
    3. Emitir NodeTraceEvent al TraceCollector
    4. Inyectar trace events en el estado retornado
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            session_id = state.get("session_id", "unknown")
            user_id = state.get("user_id", "")
            collector = get_trace_collector()
            tracer = get_tracer()

            # Pre-explanation
            explanation = ""
            if explanation_fn:
                try:
                    explanation = explanation_fn(state)
                except Exception:
                    explanation = ""

            collector.start_node(session_id, node_name, explanation)

            t0 = time.monotonic()
            try:
                # OTel span
                try:
                    from opentelemetry import trace as otel_trace
                    with tracer.start_as_current_span(
                        f"node.{node_name}",
                        attributes={
                            "node.name": node_name,
                            "node.user_id": user_id,
                            "node.session_id": session_id,
                        },
                    ) as span:
                        result = await fn(state)
                        latency = (time.monotonic() - t0) * 1000
                        span.set_attribute("node.latency_ms", latency)
                except ImportError:
                    result = await fn(state)
                    latency = (time.monotonic() - t0) * 1000

                # Post-explanation (puede usar el resultado)
                post_explanation = explanation
                if explanation_fn and not explanation:
                    try:
                        post_explanation = explanation_fn(state)
                    except Exception:
                        post_explanation = ""

                evt = collector.finish_node(session_id, node_name, latency, post_explanation)

                # Inject trace event into result
                if isinstance(result, dict):
                    existing = result.get("_trace_events", [])
                    result["_trace_events"] = existing + [evt.to_dict()]

                return result

            except Exception as exc:
                latency = (time.monotonic() - t0) * 1000
                collector.error_node(session_id, node_name, str(exc))
                raise

        return wrapper
    return decorator
