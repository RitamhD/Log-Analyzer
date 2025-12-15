from fastapi import APIRouter, Depends
from typing import List
from app.backend.schemas.event_batch import EventBatch
from app.backend.preprocessing.normalize import normalize_event
from app.backend.pipeline.dispatcher import dispatch_for_analysis


router = APIRouter()


@router.post("/")
def analyze(batch: EventBatch):
    normalized_events = [normalize_event(e) for e in batch.events]
    dispatch_for_analysis(normalized_events)
    return {
        "status": "accepted",
        "count": len(normalized_events)
    }

