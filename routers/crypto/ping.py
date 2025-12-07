# 📍 routers/crypto/ping.py
import logging
from fastapi import APIRouter
from pydantic import BaseModel

ping_router = APIRouter()
logger = logging.getLogger(__name__)


class PingResponse(BaseModel):
    status: str
    message: str

    class Config:
        # 🔹 Contoh response yang muncul di Redoc
        schema_extra = {"example": {"status": "ok", "message": "Crypto API is active"}}


@ping_router.get(
    "/ping",
    summary="Ping API",
    description="Check if the Crypto API service is online and reachable.",
    response_model=PingResponse,
    responses={
        200: {
            "description": "API is active",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "message": "Crypto API is active"}
                }
            },
        }
    },
)
async def ping():
    logger.info("🔹 Ping endpoint hit")
    return {"status": "ok", "message": "Crypto API is active"}
