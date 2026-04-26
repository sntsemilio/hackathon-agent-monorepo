"""
backend/app/observability/__init__.py
======================================

Paquete de observabilidad: OpenTelemetry, cost tracking, audit log, feature flags.
"""
from app.observability.tracer import get_tracer, setup_telemetry, trace_node  # noqa: F401
from app.observability.cost_tracker import LLMCostTracker  # noqa: F401
from app.observability.audit_log import AuditLogger  # noqa: F401
from app.observability.feature_flags import FeatureFlagService  # noqa: F401

__all__ = [
    "setup_telemetry",
    "get_tracer",
    "trace_node",
    "LLMCostTracker",
    "AuditLogger",
    "FeatureFlagService",
]
