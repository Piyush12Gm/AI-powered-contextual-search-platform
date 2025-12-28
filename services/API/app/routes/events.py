from fastapi import APIRouter
from app.schemas import EventIn
from app.kafka import get_producer

router = APIRouter()

@router.post("/publish")
async def publish_event(event: EventIn):
    producer = get_producer()
    producer.send("user-events", event.model_dump())
    return {"status": "ok"}