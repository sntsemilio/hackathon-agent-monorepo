"""
backend/scripts/agents/offline/_common.py
==========================================

Utilidades compartidas por los 4 scripts offline.

Cosas importantes detectadas en los CSVs reales de Hey Banco Datathon 2026:
    - Encoding: UTF-8 con BOM. Usar `encoding='utf-8-sig'` SIEMPRE.
    - Columna de género: el diccionario dice `genero` pero el CSV se llama `sexo`
      (valores M/H/SE). Se renombra al cargar.
    - Categorías MCC en data real incluyen valores fuera del catálogo
      (`transferencia`, `retiro_cajero`). Los modelos las tratan como buckets
      adicionales, sin romper.
    - Todos los `monto` son positivos; la dirección sale de `tipo_operacion`.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data")).resolve()
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "./backend/app/analytics/models")).resolve()
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CLIENTES_CSV = DATA_DIR / "hey_clientes.csv"
PRODUCTOS_CSV = DATA_DIR / "hey_productos.csv"
TRANSACCIONES_CSV = DATA_DIR / "hey_transacciones.csv"


# ---------------------------------------------------------------------------
# Loaders robustos
# ---------------------------------------------------------------------------
def load_clientes() -> pd.DataFrame:
    df = pd.read_csv(CLIENTES_CSV, encoding="utf-8-sig")
    if "sexo" in df.columns and "genero" not in df.columns:
        df = df.rename(columns={"sexo": "genero"})
    df["edad"] = pd.to_numeric(df["edad"], errors="coerce")
    df["ingreso_mensual_mxn"] = pd.to_numeric(df["ingreso_mensual_mxn"], errors="coerce")
    df["score_buro"] = pd.to_numeric(df["score_buro"], errors="coerce")
    df["antiguedad_dias"] = pd.to_numeric(df["antiguedad_dias"], errors="coerce")
    df["satisfaccion_1_10"] = pd.to_numeric(df["satisfaccion_1_10"], errors="coerce")
    df["dias_desde_ultimo_login"] = pd.to_numeric(df["dias_desde_ultimo_login"], errors="coerce")
    df["num_productos_activos"] = pd.to_numeric(df["num_productos_activos"], errors="coerce").fillna(0)
    for bcol in ("es_hey_pro", "nomina_domiciliada", "recibe_remesas",
                 "usa_hey_shop", "tiene_seguro", "patron_uso_atipico"):
        if bcol in df.columns:
            df[bcol] = df[bcol].astype(str).str.lower().isin({"true", "1", "yes"})
    return df


def load_productos() -> pd.DataFrame:
    df = pd.read_csv(PRODUCTOS_CSV, encoding="utf-8-sig")
    for col in ("limite_credito", "saldo_actual", "utilizacion_pct",
                "tasa_interes_anual", "monto_mensualidad"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["fecha_apertura"] = pd.to_datetime(df["fecha_apertura"], errors="coerce")
    df["fecha_ultimo_movimiento"] = pd.to_datetime(df["fecha_ultimo_movimiento"], errors="coerce")
    return df


def load_transacciones(usecols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    df = pd.read_csv(
        TRANSACCIONES_CSV,
        encoding="utf-8-sig",
        usecols=list(usecols) if usecols else None,
        low_memory=False,
    )
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    if "monto" in df.columns:
        df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0.0)
    if "es_internacional" in df.columns:
        df["es_internacional"] = df["es_internacional"].astype(str).str.lower().isin({"true", "1", "yes"})
    if "patron_uso_atipico" in df.columns:
        df["patron_uso_atipico"] = df["patron_uso_atipico"].astype(str).str.lower().isin({"true", "1", "yes"})
    return df


# ---------------------------------------------------------------------------
# Catálogos (los modelos usan estos buckets para distribuciones)
# ---------------------------------------------------------------------------
MCC_CATEGORIES = [
    "supermercado", "restaurante", "delivery", "entretenimiento", "transporte",
    "servicios_digitales", "salud", "educacion", "ropa_accesorios", "tecnologia",
    "viajes", "gobierno", "hogar", "transferencia",
]
TIPO_OPERACION = [
    "compra", "transf_salida", "transf_entrada", "retiro_cajero",
    "deposito_oxxo", "deposito_farmacia", "pago_servicio", "pago_credito",
    "abono_inversion", "retiro_inversion", "cargo_recurrente", "cashback", "devolucion",
]
CANALES = [
    "app_ios", "app_android", "app_huawei", "cajero_banregio", "cajero_externo",
    "pos_fisico", "codi", "oxxo", "farmacia_ahorro",
]
TIPOS_PRODUCTO = [
    "cuenta_debito", "tarjeta_credito_hey", "tarjeta_credito_garantizada",
    "tarjeta_credito_negocios", "credito_personal", "credito_auto", "credito_nomina",
    "inversion_hey", "seguro_vida", "seguro_compras", "cuenta_negocios",
]
PRODUCTOS_CREDITO = {
    "tarjeta_credito_hey", "tarjeta_credito_garantizada", "tarjeta_credito_negocios",
    "credito_personal", "credito_auto", "credito_nomina",
}


# ---------------------------------------------------------------------------
# Helpers de logging
# ---------------------------------------------------------------------------
def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
