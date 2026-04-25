"""
01_train_conductual.py
======================

Modelo 1 — Clustering CONDUCTUAL/DEMOGRÁFICO (K=7).

Entrena KMeans sobre features demográficas + portafolio + señales de
comportamiento. Mapea cada cluster a un nombre semántico estable.

Salidas en MODELS_DIR:
    - conductual_kmeans.joblib       (modelo + scaler + cluster_to_name)
    - conductual_features.json       (lista de features y mediana de la población)
    - conductual_assignments.parquet (user_id -> cluster -> name)

Segmentos objetivo:
    usuario_basico_bajo_enganche
    profesional_prospero_inversor
    usuario_estres_financiero
    joven_digital_hey_pro
    actividad_atipica_alerta
    empresario_alto_volumen
    cliente_promedio_estable
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from _common import (
    MODELS_DIR, banner, load_clientes, load_productos, PRODUCTOS_CREDITO,
)

K = 7
RANDOM_STATE = 42

CANDIDATE_NAMES = [
    "usuario_basico_bajo_enganche",
    "profesional_prospero_inversor",
    "usuario_estres_financiero",
    "joven_digital_hey_pro",
    "actividad_atipica_alerta",
    "empresario_alto_volumen",
    "cliente_promedio_estable",
]


def build_features() -> pd.DataFrame:
    banner("Modelo 1 — Conductual: cargando data")
    cli = load_clientes()
    prods = load_productos()

    # Agregados de productos por usuario
    g = prods.groupby("user_id", as_index=False).agg(
        n_productos=("producto_id", "count"),
        n_creditos=("tipo_producto", lambda s: s.isin(PRODUCTOS_CREDITO).sum()),
        n_inversiones=("tipo_producto", lambda s: (s == "inversion_hey").sum()),
        n_seguros=("tipo_producto", lambda s: s.isin({"seguro_vida", "seguro_compras"}).sum()),
        utilizacion_max=("utilizacion_pct", "max"),
        deuda_total=("saldo_actual", lambda s: s.fillna(0).sum()),
    )

    df = cli.merge(g, on="user_id", how="left").fillna({
        "n_productos": 0, "n_creditos": 0, "n_inversiones": 0, "n_seguros": 0,
        "utilizacion_max": 0.0, "deuda_total": 0.0,
    })

    # Codificación binaria de ocupación: empresario vs resto
    df["es_empresario"] = (df["ocupacion"] == "Empresario").astype(int)
    df["es_estudiante"] = (df["ocupacion"] == "Estudiante").astype(int)
    df["es_jubilado"] = (df["ocupacion"] == "Jubilado").astype(int)

    feature_cols = [
        "edad", "ingreso_mensual_mxn", "score_buro", "antiguedad_dias",
        "satisfaccion_1_10", "dias_desde_ultimo_login", "num_productos_activos",
        "n_creditos", "n_inversiones", "n_seguros",
        "utilizacion_max", "deuda_total",
        "es_hey_pro", "nomina_domiciliada", "recibe_remesas", "usa_hey_shop",
        "tiene_seguro", "patron_uso_atipico",
        "es_empresario", "es_estudiante", "es_jubilado",
    ]
    X = df[feature_cols].astype(float).fillna(df[feature_cols].astype(float).median())
    return df, X, feature_cols


def assign_cluster_names(centroids: np.ndarray, feature_cols: list[str]) -> dict[int, str]:
    """Heurística para mapear cluster_id -> nombre semántico."""
    df = pd.DataFrame(centroids, columns=feature_cols)

    used: set[str] = set()
    mapping: dict[int, str] = {}

    def claim(name: str, idx: int) -> None:
        if name not in used:
            mapping[idx] = name
            used.add(name)

    # 1. Alerta primero (señal más fuerte)
    if "patron_uso_atipico" in df.columns:
        idx = int(df["patron_uso_atipico"].idxmax())
        claim("actividad_atipica_alerta", idx)

    # 2. Empresario alto volumen
    if "es_empresario" in df.columns:
        scored = df["es_empresario"] * 2 + df["ingreso_mensual_mxn"] / max(df["ingreso_mensual_mxn"].max(), 1)
        for idx in scored.sort_values(ascending=False).index:
            if int(idx) not in mapping:
                claim("empresario_alto_volumen", int(idx))
                break

    # 3. Profesional próspero inversor
    scored = (df["ingreso_mensual_mxn"].rank(pct=True)
              + df["score_buro"].rank(pct=True)
              + df["n_inversiones"].rank(pct=True))
    for idx in scored.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("profesional_prospero_inversor", int(idx))
            break

    # 4. Usuario estrés financiero (alta utilización + bajo score)
    scored = df["utilizacion_max"].rank(pct=True) - df["score_buro"].rank(pct=True)
    for idx in scored.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("usuario_estres_financiero", int(idx))
            break

    # 5. Joven digital Hey Pro (joven + es_hey_pro + bajo dias_login)
    scored = (df["es_hey_pro"].rank(pct=True)
              + (1 - df["edad"].rank(pct=True))
              - df["dias_desde_ultimo_login"].rank(pct=True))
    for idx in scored.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("joven_digital_hey_pro", int(idx))
            break

    # 6. Usuario básico bajo enganche (pocos productos + alto dias_login)
    scored = df["dias_desde_ultimo_login"].rank(pct=True) - df["num_productos_activos"].rank(pct=True)
    for idx in scored.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("usuario_basico_bajo_enganche", int(idx))
            break

    # 7. Cliente promedio estable (lo que sobre)
    for idx in range(len(df)):
        if idx not in mapping:
            claim("cliente_promedio_estable", idx)
            break

    # Catch-all defensivo
    for idx in range(len(df)):
        if idx not in mapping:
            for n in CANDIDATE_NAMES:
                if n not in used:
                    claim(n, idx)
                    break
    return mapping


def main() -> None:
    df, X, feature_cols = build_features()

    banner(f"Entrenando KMeans K={K}")
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    km = KMeans(n_clusters=K, n_init=20, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_std)

    # Centroides en escala original para nombrarlos
    centroids_orig = scaler.inverse_transform(km.cluster_centers_)
    cluster_to_name = assign_cluster_names(centroids_orig, feature_cols)

    print("\nCluster -> nombre")
    for k, v in sorted(cluster_to_name.items()):
        n = int((labels == k).sum())
        print(f"  {k:>2}: {v:<35} (n={n})")

    out_model = MODELS_DIR / "conductual_kmeans.joblib"
    joblib.dump(
        {"kmeans": km, "scaler": scaler, "feature_cols": feature_cols,
         "cluster_to_name": cluster_to_name, "version": "1.0"},
        out_model,
    )
    print(f"Modelo guardado en {out_model}")

    medians = X.median().to_dict()
    (MODELS_DIR / "conductual_features.json").write_text(
        json.dumps({"feature_cols": feature_cols, "medians": medians,
                    "cluster_to_name": {str(k): v for k, v in cluster_to_name.items()}},
                   indent=2, default=str)
    )

    out_assign = MODELS_DIR / "conductual_assignments.parquet"
    pd.DataFrame({
        "user_id": df["user_id"].values,
        "cluster": labels.astype(int),
        "name": [cluster_to_name[int(c)] for c in labels],
    }).to_parquet(out_assign, index=False)
    print(f"Asignaciones guardadas en {out_assign}")


if __name__ == "__main__":
    main()
