# 📍 routers/crypto/swap.py
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

swap_router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Response Models =====
class SwapResponse(BaseModel):
    status: str
    from_token: str
    to_token: str
    swapped_amount: float
    price_from_usd: float
    price_to_usd: float

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "from_token": "SOL",
                "to_token": "USDC",
                "swapped_amount": 29.523456,
                "price_from_usd": 23.45,
                "price_to_usd": 0.78,
            }
        }


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        schema_extra = {
            "example": {"status": "error", "detail": "Failed to fetch price for SOL"}
        }


# Mapping token ke CoinGecko ID
COINGECKO_IDS = {
    "sol": "solana",
    "eth": "ethereum",
    "bnb": "binancecoin",
    "usdt": "tether",
    "usdc": "usd-coin",
    "trx": "tron",
    "ton": "the-open-network",
}


async def get_token_price_usd(token: str) -> float:
    """Fetch the token price in USD from CoinGecko"""
    token_id = COINGECKO_IDS.get(token.lower())
    if not token_id:
        raise HTTPException(status_code=400, detail=f"Token {token} is not supported")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        data = resp.json()
        price = data.get(token_id, {}).get("usd")

        if price is None:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch price for {token}"
            )

        return price


@swap_router.post(
    "/swap/simulasi",
    summary="Simulate Token Swap",
    description=(
        "Simulate swapping one token to another based on real-time CoinGecko prices. "
        "This is a simulation only and does not execute an actual transaction."
    ),
    response_model=SwapResponse,
    responses={
        200: {
            "description": "Swap simulation successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "from_token": "SOL",
                        "to_token": "USDC",
                        "swapped_amount": 29.523456,
                        "price_from_usd": 23.45,
                        "price_to_usd": 0.78,
                    }
                }
            },
        },
        400: {
            "description": "Invalid token or request",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Token XYZ is not supported",
                    }
                }
            },
        },
        500: {
            "description": "Failed to fetch price or simulation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to fetch price for SOL",
                    }
                }
            },
        },
    },
)
async def swap_tokens(
    from_token: str = Query(
        ..., description="Token symbol to swap from, e.g., SOL, ETH, USDT"
    ),
    to_token: str = Query(
        ..., description="Token symbol to swap to, e.g., ETH, USDC, SOL"
    ),
    amount: float = Query(..., description="Amount of the from_token to swap"),
):
    try:
        price_from = await get_token_price_usd(from_token)
        price_to = await get_token_price_usd(to_token)

        swapped_amount = (amount * price_from) / price_to
        swapped_amount = swapped_amount * 0.99  # apply 1% fee for simulation

        logger.info(
            f"Simulated Swap {amount} {from_token} → {swapped_amount:.6f} {to_token}"
        )

        return {
            "status": "success",
            "from_token": from_token,
            "to_token": to_token,
            "swapped_amount": round(swapped_amount, 6),
            "price_from_usd": price_from,
            "price_to_usd": price_to,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Swap simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
