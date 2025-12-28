from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, JSON, Index, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String(4000))
    category: Mapped[str] = mapped_column(String(128))
    brand: Mapped[str] = mapped_column(String(128))
    attributes: Mapped[dict] = mapped_column(JSON)
    price: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float, default=0)

    __table_args__ = (
        Index("ix_products_category", "category"),
        Index("ix_products_price", "price"),
    )

class QueryProductStats(Base):
    __tablename__ = "query_product_stats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_text: Mapped[str] = mapped_column(String(512), index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    add_to_cart: Mapped[int] = mapped_column(Integer, default=0)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    total_dwell_sec: Mapped[float] = mapped_column(Float, default=0.0)
    __table_args__ = (
        UniqueConstraint("query_text", "product_id", name="uq_query_product"),
        Index("ix_qps_query", "query_text"),
        Index("ix_qps_product", "product_id"),
    )

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)