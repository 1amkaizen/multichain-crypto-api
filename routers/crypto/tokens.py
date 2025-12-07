# 📍 routers/crypto/tokens.py
import logging
from fastapi import APIRouter
from pydantic import BaseModel

tokens_router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Response Models =====
class TokensResponse(BaseModel):
    status: str
    tokens: list[str]

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "tokens": ["BASE", "SOL", "ETH", "BNB", "TRX"],
            }
        }


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        schema_extra = {
            "example": {"status": "error", "detail": "Failed to fetch supported tokens"}
        }


@tokens_router.get(
    "/tokens",
    summary="Get Supported Tokens",
    description=(
        "Retrieve a list of tokens and blockchains supported by this API. "
        "Clients can use this list to know which tokens are available for "
        "features like token swaps, sending native tokens, or other crypto operations."
    ),
    response_model=TokensResponse,
    responses={
        200: {
            "description": "Supported tokens fetched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "tokens": ["BASE", "SOL", "ETH", "BNB", "TRX"],
                    }
                }
            },
        },
        500: {
            "description": "Failed to fetch supported tokens",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to fetch supported tokens",
                    }
                }
            },
        },
    },
)
async def get_supported_tokens():
    """
    Return the list of tokens and blockchains supported by the API.

    This helps clients to determine which tokens can be used with
    various crypto functionalities such as swap, send native, and more.
    """
    tokens = ["BASE", "SOL", "ETH", "BNB", "TRX"]
    logger.info("📌 Request for supported tokens list")
    return {"status": "success", "tokens": tokens}
