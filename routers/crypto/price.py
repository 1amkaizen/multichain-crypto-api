# 📍 routers/crypto/price.py
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from lib.coingecko import get_current_price  # ✅ import yang diperlukan

price_router = APIRouter()  # 🔹 router khusus untuk price
logger = logging.getLogger(__name__)


# ===== Response Models =====
class PriceResponse(BaseModel):
    status: str
    token: str
    price_idr: float

    class Config:
        schema_extra = {
            "example": {"status": "success", "token": "BTC", "price_idr": 450000000}
        }


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        schema_extra = {"example": {"status": "error", "detail": "Price not available"}}


@price_router.get(
    "/price",
    summary="Get Token Price",
    description="Get the real-time price of a token in IDR. The token symbol should be provided (e.g., BTC, ETH, SOL).",
    response_model=PriceResponse,
    responses={
        200: {
            "description": "Price fetched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "token": "BTC",
                        "price_idr": 450000000,
                    }
                }
            },
        },
        404: {
            "description": "Token price not available",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Price for BTC is not available",
                    }
                }
            },
        },
        500: {
            "description": "Failed to fetch token price",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to fetch token price",
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "token"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def get_token_price(
    token: str = Query(
        ...,
        description="Token symbol to fetch the current price for, e.g., BTC, ETH, SOL",
    )
):
    """
    Fetch the current real-time price of a token in Indonesian Rupiah (IDR).

    - **token**: The token symbol to get the price for (e.g., BTC, ETH, SOL)
    """
    try:
        price = await get_current_price(token)
        if price == 0:
            raise HTTPException(
                status_code=404, detail=f"Price for {token.upper()} is not available"
            )
        logger.info(f"🔹 Price fetched: {token.upper()} = {price} IDR")
        return {"status": "success", "token": token.upper(), "price_idr": price}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Failed to fetch token price: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
