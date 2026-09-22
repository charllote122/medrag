from fastapi import APIRouter
from sqlalchemy import text
from ...db.session import engine

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
