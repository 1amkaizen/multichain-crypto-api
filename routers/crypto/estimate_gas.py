# 📍 routers/crypto/estimate_gas.py
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from lib.native_sender import estimate_gas_fee  # ✅ import yang diperlukan

estimate_gas_router = APIRouter()  # 🔹 router khusus untuk estimate gas
logger = logging.getLogger(__name__)


# ===== Response Models =====
class GasFeeResponse(BaseModel):
    status: str
    gas_fee: float

    class Config:
        # 🔹 contoh response sukses
        schema_extra = {"example": {"status": "success", "gas_fee": 0.00021}}


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        # 🔹 contoh response error
        schema_extra = {
            "example": {"status": "error", "detail": "Failed to estimate gas fee"}
        }


@estimate_gas_router.get(
    "/estimate-gas",
    summary="Estimate Gas Fee",
    description="Estimate the gas fee required for sending a specific token on a selected blockchain chain.",
    response_model=GasFeeResponse,
    responses={
        200: {
            "description": "Gas fee estimated successfully",
            "content": {
                "application/json": {
                    "example": {"status": "success", "gas_fee": 0.00021}
                }
            },
        },
        500: {
            "description": "Failed to estimate gas fee",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to estimate gas fee",
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
                                "loc": ["query", "amount"],
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
async def estimate_gas(
    chain: str = Query(..., description="Blockchain chain: eth, bsc, bnb, sol, trx"),
    token: str = Query(..., description="Token symbol to send, e.g., ETH, USDT, SOL"),
    amount: float = Query(..., description="Amount of token to send"),
):
    """
    Estimate the gas fee for sending a specific token on a blockchain.

    - **chain**: Blockchain chain (eth, bsc, bnb, sol, trx)
    - **token**: Token symbol to send (e.g., ETH, USDT, SOL)
    - **amount**: Amount of token to send
    """
    try:
        # 🔹 tidak perlu wallet lagi
        gas_fee = await estimate_gas_fee(token, chain, amount)
        logger.info(f"🔹 Gas fee estimated: {gas_fee} {token} on {chain.upper()}")
        return {"status": "success", "gas_fee": gas_fee}
    except Exception as e:
        logger.error(f"❌ Failed to estimate gas fee: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
