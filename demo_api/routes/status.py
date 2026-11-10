from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api", tags=["Status"])


class ServiceStatus(BaseModel):
    service: str = Field(..., description="Service identifier")
    status: str = Field(..., description="Service operational status")
    version: str = Field(..., description="Semantic version string")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")


@router.get("/status", response_model=ServiceStatus)
def get_service_status() -> ServiceStatus:
    """Retrieve the current demo service status."""
    return ServiceStatus(
        service="demo-api",
        status="healthy",
        version="1.0.2",
        uptime_seconds=86400,
    )
