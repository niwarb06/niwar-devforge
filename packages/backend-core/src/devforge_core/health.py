from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: str


@router.get("/health/live", response_model=HealthStatus)
def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/ready", response_model=HealthStatus)
def readiness(response: Response) -> HealthStatus:
    try:
        db: Session = next(get_db())
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthStatus(status="not_ready")

    return HealthStatus(status="ready")
