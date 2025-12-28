from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.schemas import SearchQuery, SearchResult, ProductOut
from app.models import Product, QueryProductStats
from app.ai import get_text_embedding, rerank_pairs
from app.kafka import get_producer
from typing import List
import os
from qdrant_client import QdrantClient
from loguru import logger

router = APIRouter()

_QDRANT_CLIENT = None
_COLLECTION = os.getenv("QDRANT_COLLECTION", "products")
_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_qdrant():
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        _QDRANT_CLIENT = QdrantClient(url=_QDRANT_URL, timeout=2.0)
    return _QDRANT_CLIENT


@router.post("/", response_model=List[SearchResult])
async def search(q: SearchQuery, db: Session = Depends(get_db)):
    emb = get_text_embedding(q.q)
    top_k = q.top_k

    client = get_qdrant()
    # Query Qdrant for nearest neighbors (tolerate unavailability)
    try:
        search_res = client.search(collection_name=_COLLECTION, query_vector=emb, limit=top_k)
    except Exception as e:
        logger.warning(f"Qdrant search failed: {e}")
        search_res = []

    # Hydrate products from MySQL and apply structured filters
    results_raw = []
    for pt in search_res:
        prod = db.query(Product).filter(Product.id == int(pt.id)).first()
        if not prod:
            continue
        # Structured filters
        f = q.filters
        if (price := f.get("price_max")) and prod.price > float(price):
            continue
        if (price_min := f.get("price_min")) and prod.price < float(price_min):
            continue
        if (category := f.get("category")) and prod.category != str(category):
            continue
        # Multi-value categories
        cats = f.get("categories")
        if cats and str(prod.category) not in {str(c) for c in cats}:
            continue
        if (brand := f.get("brand")) and prod.brand != str(brand):
            continue
        # Multi-value brands
        brs = f.get("brands")
        if brs and str(prod.brand) not in {str(b) for b in brs}:
            continue
        if (rating_min := f.get("rating_min")) and prod.rating < float(rating_min):
            continue
        results_raw.append({
            "id": prod.id,
            "title": prod.title,
            "description": prod.description,
            "category": prod.category,
            "brand": prod.brand,
            "attributes": prod.attributes,
            "price": prod.price,
            "rating": prod.rating,
            "similarity": float(pt.score),  # Qdrant returns similarity when Distance.COSINE
        })

    candidates_text = [f"{r['title']} {r['description']}" for r in results_raw]
    rerank_scores = rerank_pairs(q.q, candidates_text) if candidates_text else []

    results: List[SearchResult] = []
    for i, r in enumerate(results_raw):
        stats = db.query(QueryProductStats).filter_by(query_text=q.q, product_id=r["id"]).first()
        ctr = (stats.clicks / stats.impressions) if stats and stats.impressions > 0 else 0
        dwell = (stats.total_dwell_sec / stats.impressions) if stats and stats.impressions > 0 else 0
        behavior_boost = 0.1 * ctr + 0.05 * min(dwell / 30.0, 1.0)
        similarity = float(r["similarity"])
        cross_score = float(rerank_scores[i]) if i < len(rerank_scores) else 0.0
        final_score = 0.6 * similarity + 0.3 * cross_score + 0.1 * behavior_boost
        explanation = (
            f"Similarity={similarity:.3f}, CrossEncoder={cross_score:.3f}, CTR={ctr:.3f}, DwellBoost={behavior_boost:.3f}"
        )
        results.append(SearchResult(
            product=ProductOut(
                id=r["id"], title=r["title"], description=r["description"], category=r["category"],
                brand=r["brand"], attributes=r["attributes"], price=r["price"], rating=r["rating"]
            ),
            score=final_score,
            explanation=explanation
        ))

    results.sort(key=lambda x: x.score, reverse=True)

    # Publish impressions for returned products
    producer = get_producer()
    for res in results:
        producer.send("user-events", {
            "type": "impression",
            "payload": {"query_text": q.q, "product_id": res.product.id}
        })

    return results