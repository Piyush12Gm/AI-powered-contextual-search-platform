import os
import json

# Lazy-initialized Kafka producer to avoid import errors when kafka-python is unavailable
_producer = None

class DummyProducer:
    def send(self, topic, value):
        # No-op: used in local preview when Kafka is not available
        return None


def get_producer():
    global _producer
    if _producer is None:
        try:
            from kafka import KafkaProducer  # import lazily to prevent startup crashes
            broker = os.getenv("KAFKA_BROKER", "kafka:9092")
            _producer = KafkaProducer(
                bootstrap_servers=[broker],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception:
            # Fallback to dummy producer so the API can start without Kafka
            _producer = DummyProducer()
    return _producer