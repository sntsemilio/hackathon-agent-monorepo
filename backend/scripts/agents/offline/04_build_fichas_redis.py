"""
04_build_fichas_redis.py
========================

Une las 3 asignaciones (conductual, transaccional, salud_financiera) en una
ficha por user_id y la persiste en Redis con key `ficha:{user_id}`.

También genera `sugerencias_candidatas` con una lógica de reglas simples
basada en los segmentos. La idea es que el agente decida si las usa o no.

Uso:
    REDIS_URL=redis://localhost:6379 \
    MODELS_DIR=./backend/app/analytics/models \
    python 04_build_fichas_redis.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import redis

from _common import MODELS_DIR, banner

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
FICHA_PREFIX = os.environ.get("FICHA_PREFIX", "ficha:")
FICHA_TTL = int(os.environ.get("FICHA_TTL_SECONDS", "0") or 0)  # 0 = sin TTL
VERSION = "1.0"


# ---------------------------------------------------------------------------
# Reglas de sugerencias por combinación de segmentos
# ---------------------------------------------------------------------------
def derive_suggestions(conductual: str, transaccional: str, salud: str) -> list[str]:
    sugs: list[str] = []

    # Salud financiera manda primero (conservador)
    if salud == "presion_financiera":
        return ["plan_pago_reestructura"]
    if salud == "en_construccion_crediticia":
        sugs.extend(["tarjeta_credito_garantizada", "cashback_hey_pro"])
    if salud == "solido_sin_credito":
        sugs.extend(["tarjeta_credito_hey", "inversion_hey"])
    if salud == "activo_saludable":
        sugs.extend(["inversion_hey", "seguro_vida"])

    # Conductual añade matiz
    if conductual == "joven_digital_hey_pro":
        sugs = ["hey_pro", "cashback_hey_pro", "codi"] + sugs
    if conductual == "profesional_prospero_inversor":
        sugs = ["inversion_hey", "seguro_vida"] + sugs
    if conductual == "empresario_alto_volumen":
        sugs = ["cuenta_negocios", "tarjeta_credito_negocios", "credito_pyme"] + sugs
    if conductual == "usuario_basico_bajo_enganche":
        sugs = ["onboarding_premium", "primer_ahorro"] + sugs
    if conductual == "usuario_estres_financiero":
        sugs = ["plan_pago_reestructura", "asesoria_financiera"] + sugs
    if conductual == "actividad_atipica_alerta":
        return ["verificacion_identidad"]

    # Transaccional ajusta producto específico
    if transaccional == "viajero_internacional":
        sugs = ["seguro_viaje", "tarjeta_credito_hey"] + sugs
    if transaccional == "consumidor_digital_ocio":
        sugs = ["cashback_hey_pro"] + sugs
    if transaccional == "ahorrador_inversor":
        sugs = ["inversion_hey", "ahorro_programado"] + sugs

    # Dedupe preservando orden
    seen, out = set(), []
    for s in sugs:
        if s not in seen:
            seen.add(s); out.append(s)
    return out[:3]


def main() -> None:
    banner("Cargando asignaciones de los 3 modelos")
    cond = pd.read_parquet(MODELS_DIR / "conductual_assignments.parquet").rename(
        columns={"cluster": "cond_cluster", "name": "cond_name"})
    trans = pd.read_parquet(MODELS_DIR / "transaccional_assignments.parquet").rename(
        columns={"cluster": "trans_cluster", "name": "trans_name"})
    salud = pd.read_parquet(MODELS_DIR / "salud_financiera_assignments.parquet").rename(
        columns={"cluster": "salud_cluster", "name": "salud_name"})

    df = cond.merge(trans, on="user_id", how="outer").merge(salud, on="user_id", how="outer")

    # Defaults defensivos para usuarios sin transacciones
    df["trans_cluster"] = df["trans_cluster"].fillna(-1).astype(int)
    df["trans_name"] = df["trans_name"].fillna("transaccional_promedio")
    df["top_spending_categories"] = df["top_spending_categories"].apply(
        lambda x: list(x) if isinstance(x, (list, tuple)) else []
    )
    df["salud_cluster"] = df["salud_cluster"].fillna(-1).astype(int)
    df["salud_name"] = df["salud_name"].fillna("en_construccion_crediticia")
    df["offer_strategy"] = df["offer_strategy"].fillna("productos_construccion_historial_y_cashback")

    print(f"Fichas a construir: {len(df):,}")

    banner(f"Conectando a Redis: {REDIS_URL}")
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("Redis OK")

    pipe = r.pipeline(transaction=False)
    n = 0
    for row in df.itertuples(index=False):
        suggestions = derive_suggestions(row.cond_name, row.trans_name, row.salud_name)
        ficha = {
            "user_id": row.user_id,
            "segmentos": {
                "conductual": {"cluster": int(row.cond_cluster), "name": row.cond_name},
                "transaccional": {
                    "cluster": int(row.trans_cluster),
                    "name": row.trans_name,
                    "top_spending_categories": list(row.top_spending_categories),
                },
                "salud_financiera": {
                    "cluster": int(row.salud_cluster),
                    "name": row.salud_name,
                    "offer_strategy": row.offer_strategy,
                },
            },
            "sugerencias_candidatas": suggestions,
            "version": VERSION,
        }
        key = f"{FICHA_PREFIX}{row.user_id}"
        if FICHA_TTL > 0:
            pipe.setex(key, FICHA_TTL, json.dumps(ficha, ensure_ascii=False))
        else:
            pipe.set(key, json.dumps(ficha, ensure_ascii=False))
        n += 1
        if n % 1000 == 0:
            pipe.execute()
            pipe = r.pipeline(transaction=False)
            print(f"  ...{n:,} fichas")
    pipe.execute()

    print(f"\nListo: {n:,} fichas escritas con prefijo `{FICHA_PREFIX}`")
    sample_key = f"{FICHA_PREFIX}{df['user_id'].iloc[0]}"
    print(f"\nEjemplo `{sample_key}`:\n{r.get(sample_key)}")


if __name__ == "__main__":
    main()
