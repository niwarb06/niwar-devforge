from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db

router = APIRouter(tags=["health"])
DbSession = Annotated[Session, Depends(get_db)]


class HealthStatus(BaseModel):
    status: str


@router.get("/health/live", response_model=HealthStatus)
def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/ready", response_model=HealthStatus)
def readiness(response: Response, db: DbSession) -> HealthStatus:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthStatus(status="not_ready")

    return HealthStatus(status="ready")
