from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import csv, io, json, os
from app.db import SessionLocal
from app.models import Base, Product
from app.schemas import ProductIn, ProductOut
from app.ai import get_text_embedding, get_embedding_dimension
from sqlalchemy import text
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

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
        _QDRANT_CLIENT = QdrantClient(url=_QDRANT_URL)
    return _QDRANT_CLIENT


@router.on_event("startup")
async def startup():
    # Ensure tables in MySQL
    try:
        with SessionLocal() as db:
            Base.metadata.create_all(bind=db.get_bind())
            db.commit()
    except Exception:
        # Tolerate startup if DB not available (e.g., local preview)
        pass
    # Ensure Qdrant collection exists
    try:
        client = get_qdrant()
        dim = get_embedding_dimension()
        try:
            client.get_collection(_COLLECTION)
        except Exception:
            try:
                client.create_collection(
                    collection_name=_COLLECTION,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                )
            except Exception:
                # Tolerate if Qdrant not reachable during startup
                pass
    except Exception:
        pass


@router.post("/ingest", response_model=list[ProductOut])
async def ingest_products_json(products: list[ProductIn], db: Session = Depends(get_db)):
    created = []
    client = get_qdrant()
    points = []
    for p in products:
        prod = Product(
            title=p.title,
            description=p.description,
            category=p.category,
            brand=p.brand,
            attributes=p.attributes,
            price=p.price,
            rating=p.rating,
        )
        db.add(prod)
        db.flush()
        emb = get_text_embedding(f"{p.title} {p.description} {p.brand} {p.category}")
        points.append(PointStruct(id=prod.id, vector=emb, payload={
            "category": p.category,
            "brand": p.brand,
            "price": p.price,
            "rating": p.rating,
        }))
        created.append(ProductOut(id=prod.id, **p.model_dump()))
    if points:
        client.upsert(collection_name=_COLLECTION, points=points)
    db.commit()
    return created


@router.post("/ingest_csv", response_model=list[ProductOut])
async def ingest_products_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode()))
    created = []
    client = get_qdrant()
    points = []
    for row in reader:
        attrs = json.loads(row.get("attributes", "{}")) if row.get("attributes") else {}
        p = ProductIn(
            title=row["title"],
            description=row["description"],
            category=row["category"],
            brand=row.get("brand", ""),
            attributes=attrs,
            price=float(row["price"]),
            rating=float(row.get("rating", 0)),
        )
        prod = Product(
            title=p.title,
            description=p.description,
            category=p.category,
            brand=p.brand,
            attributes=p.attributes,
            price=p.price,
            rating=p.rating,
        )
        db.add(prod)
        db.flush()
        emb = get_text_embedding(f"{p.title} {p.description} {p.brand} {p.category}")
        points.append(PointStruct(id=prod.id, vector=emb, payload={
            "category": p.category,
            "brand": p.brand,
            "price": p.price,
            "rating": p.rating,
        }))
        created.append(ProductOut(id=prod.id, **p.model_dump()))
    if points:
        client.upsert(collection_name=_COLLECTION, points=points)
    db.commit()
    return created