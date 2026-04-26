"""
Clear and regenerate fichas in Redis with proper kmeans segmentation.
"""
import redis
import json
import logging
from pathlib import Path
from app.analytics.engine import AnalyticsEngine
from app.agents.micro_agents.ficha_injector import _suggestions_from_segments, _generate_default_features
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Connect to Redis
    settings = get_settings()
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    # Clear existing fichas
    print("🗑️  Clearing existing fichas...")
    ficha_keys = list(r.scan_iter("ficha:*"))
    if ficha_keys:
        r.delete(*ficha_keys)
        print(f"   Deleted {len(ficha_keys)} old fichas")
    else:
        print("   No existing fichas found")

    # Initialize analytics engine with kmeans models
    print("\n🤖 Loading kmeans models...")
    engine = AnalyticsEngine(settings.MODELS_DIR)
    engine.load()

    if not engine.fully_loaded:
        print("❌ ERROR: Could not load all kmeans models!")
        return
    print("✅ Kmeans models loaded successfully")

    # Generate sample fichas with proper kmeans segmentation
    print("\n📝 Generating 10 sample fichas with kmeans segmentation...")
    sample_user_ids = [
        "user_001", "user_002", "user_003", "user_004", "user_005",
        "user_006", "user_007", "user_008", "user_009", "user_010",
    ]

    for user_id in sample_user_ids:
        # Generate default features (same as what ficha_injector now uses)
        features = _generate_default_features()

        # Predict segments using kmeans
        segs = engine.predict_segments_for_user(user_id, features=features)

        # Create ficha
        ficha = {
            "user_id": user_id,
            "segmentos": segs,
            "sugerencias_candidatas": _suggestions_from_segments(segs),
            "version": "kmeans-1.0",
        }

        # Store in Redis
        key = f"ficha:{user_id}"
        r.set(key, json.dumps(ficha))

        cond = segs.get("conductual", {}).get("name", "?")
        salud = segs.get("salud_financiera", {}).get("name", "?")
        print(f"   {user_id}: {cond} / {salud}")

    print("\n✅ Done! Fichas regenerated with proper kmeans segmentation")
    print(f"   Total ficha keys in Redis: {len(list(r.scan_iter('ficha:*')))}")

if __name__ == "__main__":
    main()
