from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Any

import joblib

from app.core.config import get_settings


@dataclass(slots=True)
class LoadedModel:
    """Container for an artifact loaded from disk."""

    name: str
    path: Path
    artifact: Any = field(repr=False)


class AnalyticsEngine:
    """Singleton engine that serves analytical user insights from classical ML artifacts."""

    _instance: AnalyticsEngine | None = None
    _singleton_lock: Lock = Lock()

    def __new__(cls) -> AnalyticsEngine:
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        settings = get_settings()
        self._models_dir = Path(settings.analytics_models_dir)
        self._loaded_models: dict[str, LoadedModel] = {}
        self._models_loaded = False
        self._initialized = True

    @property
    def models_loaded(self) -> bool:
        """Return whether at least one analytics artifact is loaded."""

        return self._models_loaded

    @property
    def model_names(self) -> list[str]:
        """Return loaded model names."""

        return sorted(self._loaded_models.keys())

    def load_models(self) -> None:
        """Load .pkl and .joblib artifacts from the configured model directory.

        Invalid or corrupted artifacts are skipped to keep startup resilient.
        """

        self._models_dir.mkdir(parents=True, exist_ok=True)
        discovered_paths = sorted(self._models_dir.glob("*.pkl")) + sorted(
            self._models_dir.glob("*.joblib")
        )

        loaded_models: dict[str, LoadedModel] = {}
        for model_path in discovered_paths:
            try:
                artifact = joblib.load(model_path)
            except (EOFError, FileNotFoundError, OSError, TypeError, ValueError):
                continue

            loaded_models[model_path.stem] = LoadedModel(
                name=model_path.stem,
                path=model_path,
                artifact=artifact,
            )

        self._loaded_models = loaded_models
        self._models_loaded = bool(loaded_models)

    async def get_user_insights(self, user_id: str) -> dict[str, Any]:
        """Return structured analytics insights for a user.

        The current implementation returns deterministic mock insights, while exposing
        model metadata to ease future migration to real estimators.
        """

        normalized_user_id = user_id.strip() or "anonymous"
        digest = sha256(normalized_user_id.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)

        score = 45 + (seed % 56)
        spending_variability = 10 + (seed % 65)
        avg_monthly_tickets = 2 + (seed % 18)
        churn_risk = round((seed % 100) / 100, 2)

        segment_candidates = [
            "ahorrador_prudente",
            "inversionista_curioso",
            "crecimiento_acelerado",
            "conservador_digital",
        ]
        segment = segment_candidates[seed % len(segment_candidates)]

        if score >= 80:
            financial_label = "solida"
        elif score >= 60:
            financial_label = "estable"
        else:
            financial_label = "vulnerable"

        return {
            "user_id": normalized_user_id,
            "perfil_cliente": {
                "segmento": segment,
                "canal_preferido": "digital",
                "sensibilidad_riesgo": "media" if score >= 60 else "alta",
            },
            "salud_financiera": {
                "score": score,
                "categoria": financial_label,
                "churn_risk": churn_risk,
            },
            "comportamiento_transaccional": {
                "variabilidad_gasto": spending_variability,
                "tickets_mensuales_promedio": avg_monthly_tickets,
                "pico_consumo_fin_de_mes": bool(seed % 2),
            },
            "metadata_analitica": {
                "models_loaded": self.models_loaded,
                "available_models": self.model_names,
            },
        }
