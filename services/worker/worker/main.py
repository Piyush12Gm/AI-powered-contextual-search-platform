import os
import json
import time
from kafka import KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@db:3306/lenskart")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

consumer = KafkaConsumer(
    "user-events",
    bootstrap_servers=os.getenv("KAFKA_BROKER", "kafka:9092"),
    group_id=os.getenv("KAFKA_GROUP_ID", "stats-worker"),
    enable_auto_commit=True,
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

from worker.stats import process_event

if __name__ == "__main__":
    session = SessionLocal()
    try:
        for message in consumer:
            event = message.value
            try:
                process_event(session, event)
                session.commit()
            except Exception:
                session.rollback()
            time.sleep(0.01)
    finally:
        session.close()