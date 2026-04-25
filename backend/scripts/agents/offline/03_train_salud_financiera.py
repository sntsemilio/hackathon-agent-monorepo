"""
03_train_salud_financiera.py
============================

Modelo 3 — SALUD FINANCIERA (K=4).

Propósito (importante): NO es para riesgo o fraude (Hey Banco ya tiene eso).
Es para decidir qué tipo de conversación financiera es apropiada y qué NO
ofrecer. Por eso el output incluye una `offer_strategy`.

Features por user_id:
    - score_buro
    - utilizacion_credito_avg / utilizacion_credito_max
    - ratio_deuda_ingreso (deuda total / (ingreso_mensual_mxn * 12))
    - n_fallos_pago_financieros (no_procesada por saldo_insuficiente,
      limite_excedido, monto_excede_limite_diario)
    - abonos_inversion_total
    - capacidad_ahorro_proxy = ingresos - egresos del mes promedio

Segmentos:
    solido_sin_credito          -> "ofrecer_primer_credito_o_inversion"
    en_construccion_crediticia  -> "productos_construccion_historial_y_cashback"
    activo_saludable            -> "inversion_seguros_premium"
    presion_financiera          -> "alivio_planes_pago_NO_aumentar_deuda"
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from _common import (
    MODELS_DIR, PRODUCTOS_CREDITO, banner,
    load_clientes, load_productos, load_transacciones,
)

K = 4
RANDOM_STATE = 42

CLUSTER_TO_OFFER = {
    "solido_sin_credito": "ofrecer_primer_credito_o_inversion",
    "en_construccion_crediticia": "productos_construccion_historial_y_cashback",
    "activo_saludable": "inversion_seguros_premium",
    "presion_financiera": "alivio_planes_pago_NO_aumentar_deuda",
}

FALLOS_FIN = {"saldo_insuficiente", "limite_excedido", "monto_excede_limite_diario"}


def build_features() -> pd.DataFrame:
    banner("Modelo 3 — Salud Financiera: cargando data")
    cli = load_clientes()
    prods = load_productos()
    cols_tx = ["user_id", "tipo_operacion", "monto", "estatus",
               "motivo_no_procesada", "fecha_hora"]
    tx = load_transacciones(usecols=cols_tx)

    # Por usuario: utilización y deuda
    creds = prods[prods["tipo_producto"].isin(PRODUCTOS_CREDITO)]
    util = creds.groupby("user_id").agg(
        util_avg=("utilizacion_pct", "mean"),
        util_max=("utilizacion_pct", "max"),
        deuda_total=("saldo_actual", lambda s: s.fillna(0).sum()),
        n_creditos=("producto_id", "count"),
    )

    # Fallos por razones financieras
    failed = tx[(tx["estatus"] == "no_procesada")
                & (tx["motivo_no_procesada"].isin(FALLOS_FIN))]
    n_fallos = failed.groupby("user_id").size().rename("n_fallos_financieros")

    # Abonos a inversión (total)
    inv = tx[(tx["tipo_operacion"] == "abono_inversion") & (tx["estatus"] == "completada")]
    inv_total = inv.groupby("user_id")["monto"].sum().rename("abonos_inversion_total")

    # Capacidad de ahorro proxy: gastos / ingresos
    GASTOS = {"compra", "transf_salida", "pago_servicio", "pago_credito",
              "cargo_recurrente", "retiro_cajero"}
    INGRESOS = {"transf_entrada", "deposito_oxxo", "deposito_farmacia"}
    completed = tx[tx["estatus"] == "completada"]
    g = completed[completed["tipo_operacion"].isin(GASTOS)].groupby("user_id")["monto"].sum()
    i = completed[completed["tipo_operacion"].isin(INGRESOS)].groupby("user_id")["monto"].sum()
    flujo = pd.DataFrame({"egresos_total": g, "ingresos_total": i}).fillna(0.0)
    flujo["capacidad_ahorro_proxy"] = flujo["ingresos_total"] - flujo["egresos_total"]

    df = cli[["user_id", "score_buro", "ingreso_mensual_mxn"]].merge(
        util, on="user_id", how="left"
    ).merge(n_fallos, on="user_id", how="left").merge(
        inv_total, on="user_id", how="left"
    ).merge(flujo, on="user_id", how="left").fillna(0.0)

    df["ratio_deuda_ingreso"] = df["deuda_total"] / (df["ingreso_mensual_mxn"] * 12).replace(0, np.nan)
    df["ratio_deuda_ingreso"] = df["ratio_deuda_ingreso"].fillna(0.0).clip(0, 5)
    df["log_inv"] = np.log1p(df["abonos_inversion_total"])
    df["log_ahorro_proxy"] = np.sign(df["capacidad_ahorro_proxy"]) * np.log1p(df["capacidad_ahorro_proxy"].abs())

    feats = df.drop(columns=["ingreso_mensual_mxn", "egresos_total", "ingresos_total",
                              "abonos_inversion_total", "capacidad_ahorro_proxy"])
    return feats


def assign_names(centroids: pd.DataFrame) -> dict[int, str]:
    used: set[str] = set()
    mapping: dict[int, str] = {}

    def claim(name: str, idx: int):
        if name not in used:
            mapping[idx] = name
            used.add(name)

    # 1. presion_financiera: util alta + fallos + bajo score
    pressure = (centroids["util_max"].rank(pct=True)
                + centroids["n_fallos_financieros"].rank(pct=True)
                - centroids["score_buro"].rank(pct=True))
    for idx in pressure.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("presion_financiera", int(idx))
            break

    # 2. activo_saludable: alto score + abonos inversión + bajo util
    healthy = (centroids["score_buro"].rank(pct=True)
               + centroids["log_inv"].rank(pct=True)
               - centroids["util_avg"].rank(pct=True))
    for idx in healthy.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("activo_saludable", int(idx))
            break

    # 3. solido_sin_credito: alto score + n_creditos cerca de 0
    solid = centroids["score_buro"].rank(pct=True) - centroids["n_creditos"].rank(pct=True)
    for idx in solid.sort_values(ascending=False).index:
        if int(idx) not in mapping:
            claim("solido_sin_credito", int(idx))
            break

    # 4. en_construccion_crediticia: lo que sobre
    for idx in range(len(centroids)):
        if idx not in mapping:
            claim("en_construccion_crediticia", idx)
            break
    for idx in range(len(centroids)):
        if idx not in mapping:
            for n in CLUSTER_TO_OFFER:
                if n not in used:
                    claim(n, idx); break
    return mapping


def main() -> None:
    feats = build_features()
    user_ids = feats["user_id"].values
    X = feats.drop(columns=["user_id"]).fillna(0.0).values

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    banner(f"Entrenando KMeans K={K}")
    km = KMeans(n_clusters=K, n_init=20, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_std)

    centroids_df = pd.DataFrame(
        scaler.inverse_transform(km.cluster_centers_),
        columns=feats.drop(columns=["user_id"]).columns,
    )
    cluster_to_name = assign_names(centroids_df)
    cluster_to_offer = {k: CLUSTER_TO_OFFER[v] for k, v in cluster_to_name.items()}

    print("\nCluster -> nombre / offer_strategy")
    for k, v in sorted(cluster_to_name.items()):
        n = int((labels == k).sum())
        print(f"  {k:>2}: {v:<28} -> {cluster_to_offer[k]:<48} (n={n})")

    out = MODELS_DIR / "salud_financiera_kmeans.joblib"
    joblib.dump({
        "kmeans": km, "scaler": scaler,
        "feature_cols": list(feats.drop(columns=["user_id"]).columns),
        "cluster_to_name": cluster_to_name,
        "cluster_to_offer": cluster_to_offer,
        "version": "1.0",
    }, out)
    print(f"Modelo guardado en {out}")

    (MODELS_DIR / "salud_financiera_features.json").write_text(json.dumps({
        "cluster_to_name": {str(k): v for k, v in cluster_to_name.items()},
        "cluster_to_offer": {str(k): v for k, v in cluster_to_offer.items()},
    }, indent=2))

    out_assign = MODELS_DIR / "salud_financiera_assignments.parquet"
    pd.DataFrame({
        "user_id": user_ids,
        "cluster": labels.astype(int),
        "name": [cluster_to_name[int(c)] for c in labels],
        "offer_strategy": [cluster_to_offer[int(c)] for c in labels],
    }).to_parquet(out_assign, index=False)
    print(f"Asignaciones guardadas en {out_assign}")


if __name__ == "__main__":
    main()
