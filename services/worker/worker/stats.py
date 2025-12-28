from sqlalchemy.orm import Session
from sqlalchemy import text


def process_event(db: Session, event: dict):
    etype = event.get("type")
    payload = event.get("payload", {})
    # Simplified payload expected keys: query_text, product_id, dwell_sec
    query_text = payload.get("query_text")
    product_id = payload.get("product_id")
    dwell_sec = float(payload.get("dwell_sec", 0))

    if not (query_text and product_id):
        return

    # Upsert stats row (MySQL): insert if not exists due to unique constraint
    upsert_sql = text(
        """
        INSERT IGNORE INTO query_product_stats (
            query_text, product_id, clicks, add_to_cart, purchases, impressions, total_dwell_sec
        ) VALUES (:query_text, :product_id, 0, 0, 0, 0, 0)
        """
    )
    try:
        db.execute(upsert_sql, {"query_text": query_text, "product_id": int(product_id)})
    except Exception:
        pass

    if etype == "impression":
        db.execute(
            text(
                "UPDATE query_product_stats SET impressions = impressions + 1 WHERE query_text = :q AND product_id = :pid"
            ),
            {"q": query_text, "pid": int(product_id)},
        )
    elif etype == "click":
        db.execute(
            text("UPDATE query_product_stats SET clicks = clicks + 1 WHERE query_text = :q AND product_id = :pid"),
            {"q": query_text, "pid": int(product_id)},
        )
    elif etype == "add_to_cart":
        db.execute(
            text(
                "UPDATE query_product_stats SET add_to_cart = add_to_cart + 1 WHERE query_text = :q AND product_id = :pid"
            ),
            {"q": query_text, "pid": int(product_id)},
        )
    elif etype == "purchase":
        db.execute(
            text("UPDATE query_product_stats SET purchases = purchases + 1 WHERE query_text = :q AND product_id = :pid"),
            {"q": query_text, "pid": int(product_id)},
        )
    if dwell_sec:
        db.execute(
            text(
                "UPDATE query_product_stats SET total_dwell_sec = total_dwell_sec + :d WHERE query_text = :q AND product_id = :pid"
            ),
            {"q": query_text, "pid": int(product_id), "d": dwell_sec},
        )