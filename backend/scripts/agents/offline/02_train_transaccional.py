"""
02_train_transaccional.py
=========================

Modelo 2 — Clustering TRANSACCIONAL (K elegido por silhouette en {4,5,6,7}).

Features por user_id:
    - distribución porcentual de gasto por categoría MCC (14)
    - mix de canales (% por canal)
    - mix de tipos de operación (% por tipo)
    - patrón temporal: %tx en horario noche (22-06), %fin de semana
    - ticket promedio (log1p), recency (días desde última tx)

Solo se usan transacciones con `estatus == 'completada'` y `tipo_operacion`
de gasto (compra, transf_salida, pago_servicio, pago_credito, cargo_recurrente,
abono_inversion).

Salidas:
    - transaccional_kmeans.joblib
    - transaccional_features.json
    - transaccional_assignments.parquet
"""
from __future__ import annotations

import json
from collections import defaultdict

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from _common import (
    CANALES, MCC_CATEGORIES, MODELS_DIR, TIPO_OPERACION,
    banner, load_transacciones,
)

GASTO_OPS = {"compra", "transf_salida", "pago_servicio", "pago_credito",
             "cargo_recurrente", "abono_inversion"}
RANDOM_STATE = 42

CANDIDATE_NAMES = [
    "consumidor_digital_ocio",
    "pagador_servicios_hogar",
    "comprador_presencial_frecuente",
    "viajero_internacional",
    "ahorrador_inversor",
    "transaccional_promedio",
]


def build_features() -> pd.DataFrame:
    banner("Modelo 2 — Transaccional: cargando data")
    cols = ["user_id", "fecha_hora", "tipo_operacion", "canal", "monto",
            "categoria_mcc", "estatus", "hora_del_dia", "dia_semana", "es_internacional"]
    tx = load_transacciones(usecols=cols)
    tx = tx[tx["estatus"] == "completada"]
    tx = tx[tx["tipo_operacion"].isin(GASTO_OPS)]
    tx = tx.dropna(subset=["user_id", "monto"])
    tx["categoria_mcc"] = tx["categoria_mcc"].fillna("transferencia")
    tx["canal"] = tx["canal"].fillna("app_ios")
    tx["dia_semana"] = tx["dia_semana"].fillna("Monday")

    # Distribución MCC en %
    mcc = tx.groupby(["user_id", "categoria_mcc"])["monto"].sum().unstack(fill_value=0.0)
    for c in MCC_CATEGORIES:
        if c not in mcc.columns:
            mcc[c] = 0.0
    mcc = mcc[MCC_CATEGORIES]
    mcc = mcc.div(mcc.sum(axis=1).replace(0, 1), axis=0).add_prefix("mcc_")

    # Mix canales
    chn = tx.groupby(["user_id", "canal"])["monto"].count().unstack(fill_value=0.0)
    for c in CANALES:
        if c not in chn.columns:
            chn[c] = 0.0
    chn = chn[CANALES].div(chn[CANALES].sum(axis=1).replace(0, 1), axis=0).add_prefix("chn_")

    # Mix tipo_operacion
    op = tx.groupby(["user_id", "tipo_operacion"])["monto"].count().unstack(fill_value=0.0)
    for c in TIPO_OPERACION:
        if c not in op.columns:
            op[c] = 0.0
    op = op[TIPO_OPERACION].div(op[TIPO_OPERACION].sum(axis=1).replace(0, 1), axis=0).add_prefix("op_")

    # Temporales
    tx["es_finde"] = tx["dia_semana"].isin(["Saturday", "Sunday"]).astype(int)
    tx["es_noche"] = tx["hora_del_dia"].apply(lambda h: 1 if (pd.notna(h) and (h >= 22 or h <= 6)) else 0)
    temp = tx.groupby("user_id").agg(
        pct_finde=("es_finde", "mean"),
        pct_noche=("es_noche", "mean"),
        pct_internacional=("es_internacional", "mean"),
        ticket_avg=("monto", "mean"),
        n_tx=("monto", "count"),
        last_tx=("fecha_hora", "max"),
    )
    ref_date = tx["fecha_hora"].max()
    temp["recency_days"] = (ref_date - temp["last_tx"]).dt.days.fillna(9999)
    temp = temp.drop(columns=["last_tx"])
    temp["log_ticket_avg"] = np.log1p(temp["ticket_avg"].fillna(0))
    temp["log_n_tx"] = np.log1p(temp["n_tx"].fillna(0))

    feats = mcc.join(chn, how="outer").join(op, how="outer").join(temp, how="outer").fillna(0.0)
    feats = feats.reset_index()
    return feats


def best_k(X_std: np.ndarray, ks=(4, 5, 6, 7)) -> tuple[int, dict[int, float]]:
    sample = X_std if len(X_std) <= 5000 else X_std[
        np.random.default_rng(RANDOM_STATE).choice(len(X_std), 5000, replace=False)
    ]
    scores = {}
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
        labels = km.fit_predict(sample)
        try:
            scores[k] = float(silhouette_score(sample, labels))
        except Exception:
            scores[k] = -1.0
        print(f"  K={k} silhouette={scores[k]:.4f}")
    return max(scores, key=scores.get), scores


def assign_names(centroids: pd.DataFrame) -> dict[int, str]:
    used: set[str] = set()
    mapping: dict[int, str] = {}

    def claim(name: str, idx: int) -> None:
        if name not in used:
            mapping[idx] = name
            used.add(name)

    # 1. viajero_internacional
    if "pct_internacional" in centroids.columns:
        idx = int(centroids["pct_internacional"].idxmax())
        claim("viajero_internacional", idx)

    # 2. ahorrador_inversor
    if "op_abono_inversion" in centroids.columns:
        idx = int(centroids["op_abono_inversion"].idxmax())
        if idx not in mapping:
            claim("ahorrador_inversor", idx)

    # 3. consumidor_digital_ocio
    digital = (centroids.get("mcc_servicios_digitales", 0)
               + centroids.get("mcc_entretenimiento", 0))
    for idx in digital.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("consumidor_digital_ocio", int(idx))
            break

    # 4. pagador_servicios_hogar
    home = centroids.get("mcc_hogar", 0) + centroids.get("op_pago_servicio", 0)
    for idx in home.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("pagador_servicios_hogar", int(idx))
            break

    # 5. comprador_presencial_frecuente
    pres = centroids.get("chn_pos_fisico", 0)
    for idx in pres.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("comprador_presencial_frecuente", int(idx))
            break

    # 6. promedio
    for idx in range(len(centroids)):
        if idx not in mapping:
            claim("transaccional_promedio", idx)
            break
    for idx in range(len(centroids)):
        if idx not in mapping:
            for n in CANDIDATE_NAMES:
                if n not in used:
                    claim(n, idx); break
    return mapping


def top_categories_by_cluster(feats: pd.DataFrame, labels: np.ndarray) -> dict[int, list[str]]:
    """Top 2 categorías de gasto promedio por cluster."""
    df = feats.copy()
    df["cluster"] = labels
    mcc_cols = [c for c in df.columns if c.startswith("mcc_")]
    centroids = df.groupby("cluster")[mcc_cols].mean()
    top: dict[int, list[str]] = {}
    for c in centroids.index:
        sorted_cats = centroids.loc[c].sort_values(ascending=False)
        top[int(c)] = [s.replace("mcc_", "") for s in sorted_cats.index[:2]]
    return top


def main() -> None:
    feats = build_features()
    user_ids = feats["user_id"].values
    X = feats.drop(columns=["user_id"]).fillna(0.0).values

    banner("Estandarizando + buscando K óptimo")
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)
    K, scores = best_k(X_std)
    print(f"\nK seleccionado: {K}")

    km = KMeans(n_clusters=K, n_init=20, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_std)

    centroids_df = pd.DataFrame(
        scaler.inverse_transform(km.cluster_centers_),
        columns=feats.drop(columns=["user_id"]).columns,
    )
    cluster_to_name = assign_names(centroids_df)
    top_cats = top_categories_by_cluster(feats, labels)

    print("\nCluster -> nombre (top categorías)")
    for k, v in sorted(cluster_to_name.items()):
        n = int((labels == k).sum())
        print(f"  {k:>2}: {v:<35} top={top_cats.get(k)} (n={n})")

    out = MODELS_DIR / "transaccional_kmeans.joblib"
    joblib.dump({
        "kmeans": km, "scaler": scaler,
        "feature_cols": list(feats.drop(columns=["user_id"]).columns),
        "cluster_to_name": cluster_to_name,
        "top_categories": top_cats,
        "k_selected": K, "k_scores": scores,
        "version": "1.0",
    }, out)
    print(f"Modelo guardado en {out}")

    (MODELS_DIR / "transaccional_features.json").write_text(json.dumps({
        "k_selected": K, "k_scores": scores,
        "cluster_to_name": {str(k): v for k, v in cluster_to_name.items()},
        "top_categories": {str(k): v for k, v in top_cats.items()},
    }, indent=2))

    out_assign = MODELS_DIR / "transaccional_assignments.parquet"
    pd.DataFrame({
        "user_id": user_ids,
        "cluster": labels.astype(int),
        "name": [cluster_to_name[int(c)] for c in labels],
        "top_spending_categories": [top_cats[int(c)] for c in labels],
    }).to_parquet(out_assign, index=False)
    print(f"Asignaciones guardadas en {out_assign}")


if __name__ == "__main__":
    main()
