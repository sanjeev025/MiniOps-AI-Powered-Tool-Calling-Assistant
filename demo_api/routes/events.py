from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api", tags=["Events"])


class EventItem(BaseModel):
    event: str = Field(..., description="Description of the event")
    time: str = Field(..., description="Timestamp or time string of the event")


class RecentEventsResponse(BaseModel):
    events: List[EventItem] = Field(..., description="List of recent events")


@router.get("/events", response_model=RecentEventsResponse)
def get_recent_events() -> RecentEventsResponse:
    """Retrieve recent application events."""
    return RecentEventsResponse(
        events=[
            EventItem(event="Application restarted", time="10:30 AM"),
            EventItem(event="Configuration updated", time="11:15 AM"),
        ]
    )
