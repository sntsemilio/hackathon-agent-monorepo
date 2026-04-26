"""
Load dataset_transacciones CSVs into Redis for RAG.
"""
import os
import sys
import pandas as pd
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from redisvl.index import AsyncSearchIndex
from redisvl.utils.vectorize import HFTextVectorizer


async def load_dataset():
    settings = get_settings()
    dataset_path = Path("/Users/nicoromero/Downloads/dataset_transacciones")

    if not dataset_path.exists():
        print(f"❌ Dataset path not found: {dataset_path}")
        return

    print(f"📂 Loading from: {dataset_path}")

    # Initialize vectorizer
    vectorizer = HFTextVectorizer(model=settings.EMBED_MODEL)

    # Initialize RedisVL index
    try:
        index = AsyncSearchIndex.from_existing(
            name=settings.REDIS_INDEX_NAME,
            redis_url=settings.REDIS_URL,
        )
        print(f"✅ Connected to index: {settings.REDIS_INDEX_NAME}")
    except Exception as e:
        print(f"⚠️  Index doesn't exist, will create one: {e}")
        index = None

    # Load CSVs
    documents = []

    # Load transacciones
    print("\n📥 Loading hey_transacciones.csv...")
    df_trans = pd.read_csv(dataset_path / "hey_transacciones.csv", nrows=1000)  # Limit for demo
    for idx, row in df_trans.iterrows():
        doc_text = f"Transacción {row.get('id', idx)}: {row.get('descripcion', '')} - Monto: {row.get('monto', '')} - Estado: {row.get('estado', '')}"
        documents.append({
            "id": f"trans_{idx}",
            "text": doc_text,
            "title": f"Transacción {idx}",
            "source": "hey_transacciones",
        })

    # Load productos
    print("📥 Loading hey_productos.csv...")
    df_prod = pd.read_csv(dataset_path / "hey_productos.csv")
    for idx, row in df_prod.iterrows():
        doc_text = f"Producto: {row.get('nombre', '')} - {row.get('descripcion', '')} - Beneficios: {row.get('beneficios', '')}"
        documents.append({
            "id": f"prod_{idx}",
            "text": doc_text,
            "title": row.get('nombre', f'Producto {idx}'),
            "source": "hey_productos",
        })

    # Load clientes
    print("📥 Loading hey_clientes.csv...")
    df_clientes = pd.read_csv(dataset_path / "hey_clientes.csv", nrows=100)
    for idx, row in df_clientes.iterrows():
        doc_text = f"Cliente: {row.get('nombre', '')} - Segmento: {row.get('segmento', '')} - Estado: {row.get('estado', '')}"
        documents.append({
            "id": f"cliente_{idx}",
            "text": doc_text,
            "title": f"Cliente {idx}",
            "source": "hey_clientes",
        })

    print(f"\n✅ Prepared {len(documents)} documents")

    # Add embeddings
    print("\n🔄 Generating embeddings...")
    for i, doc in enumerate(documents):
        if i % 100 == 0:
            print(f"  {i}/{len(documents)}")
        doc["embedding"] = vectorizer.embed(doc["text"], as_buffer=True)

    # Store in Redis
    print("\n💾 Storing in Redis...")
    from redis import Redis
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)

    for i, doc in enumerate(documents):
        if i % 100 == 0:
            print(f"  {i}/{len(documents)}")

        # Store as hash
        key = f"{settings.REDIS_INDEX_NAME}:{doc['id']}"
        redis_client.hset(
            key,
            mapping={
                "text": doc["text"],
                "title": doc["title"],
                "source": doc["source"],
                "embedding": doc["embedding"],
            }
        )

    redis_client.close()
    print(f"\n✅ Done! Stored {len(documents)} documents in Redis")
    print(f"   Index name: {settings.REDIS_INDEX_NAME}")
    print(f"   Redis URL: {settings.REDIS_URL}")


if __name__ == "__main__":
    asyncio.run(load_dataset())
