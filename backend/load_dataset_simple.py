"""
Simple dataset loader - sin embeddings vectoriales, solo BM25.
"""
import pandas as pd
import redis
from pathlib import Path

# Connect to Redis
r = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)

dataset_path = Path("/Users/nicoromero/Downloads/dataset_transacciones")

print("📥 Loading CSV files...")

# Load transacciones (sample)
print("  - hey_transacciones.csv")
df_trans = pd.read_csv(dataset_path / "hey_transacciones.csv", nrows=500)
for idx, row in df_trans.iterrows():
    key = f"doc:trans:{idx}"
    r.hset(key, mapping={
        "text": f"{row.get('descripcion', '')} {row.get('estado', '')}",
        "title": f"Transacción {idx}",
        "source": "transacciones",
        "monto": str(row.get('monto', '')),
    })

# Load productos
print("  - hey_productos.csv")
df_prod = pd.read_csv(dataset_path / "hey_productos.csv")
for idx, row in df_prod.iterrows():
    key = f"doc:prod:{idx}"
    r.hset(key, mapping={
        "text": f"{row.get('nombre', '')} {row.get('descripcion', '')} {row.get('beneficios', '')}",
        "title": row.get('nombre', f'Producto {idx}'),
        "source": "productos",
    })

# Load clientes (sample)
print("  - hey_clientes.csv")
df_clientes = pd.read_csv(dataset_path / "hey_clientes.csv", nrows=100)
for idx, row in df_clientes.iterrows():
    key = f"doc:cliente:{idx}"
    r.hset(key, mapping={
        "text": f"{row.get('nombre', '')} {row.get('segmento', '')} {row.get('estado', '')}",
        "title": f"Cliente {idx}",
        "source": "clientes",
    })

# Add hardcoded FAQ about transaction blocks
faq_docs = [
    {
        "id": "faq:bloqueo_1",
        "text": "Las transacciones pueden ser bloqueadas por motivos de seguridad. Si detectamos actividad inusual en tu cuenta, podemos bloquear transacciones temporalmente para protegerte de fraude.",
        "title": "¿Por qué se bloquean transacciones?",
        "source": "faq",
    },
    {
        "id": "faq:bloqueo_2",
        "text": "Si tu transacción fue bloqueada, puede ser por: 1) Monto inusual, 2) Ubicación geográfica sospechosa, 3) Patrón de gasto atípico, 4) Cuenta con actividad de riesgo.",
        "title": "Razones comunes de bloqueo",
        "source": "faq",
    },
    {
        "id": "faq:desbloquear",
        "text": "Para desbloquear tu cuenta, puedes: 1) Verificar tu identidad en la app, 2) Confirmar el patrón de gasto, 3) Contactar al equipo de seguridad, 4) Esperar 24 horas.",
        "title": "Cómo desbloquear una transacción",
        "source": "faq",
    },
]

print("  - Agregando FAQ...")
for doc in faq_docs:
    r.hset(f"doc:{doc['id']}", mapping={
        "text": doc["text"],
        "title": doc["title"],
        "source": doc["source"],
    })

total = r.dbsize()
print(f"\n✅ Done! Total keys in Redis: {total}")
print("   Documentos cargados para búsqueda BM25")
