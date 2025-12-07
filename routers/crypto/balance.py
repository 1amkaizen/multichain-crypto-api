# 📍 routers/crypto/balance.py
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from lib.balance_checker import check_balance

balance_router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Response Model =====
class BalanceResponse(BaseModel):
    status: str
    chain: str
    wallet: str
    balance: float

    class Config:
        # 🔹 Contoh response sukses
        schema_extra = {
            "example": {
                "status": "success",
                "chain": "ETH",
                "wallet": "0x1234...abcd",
                "balance": 12.34,
            }
        }


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        # 🔹 Contoh response error
        schema_extra = {
            "example": {
                "status": "error",
                "detail": "Failed to connect to RPC URL",
            }
        }


@balance_router.get(
    "/balance",
    summary="Get Wallet Balance",
    description="Check the balance of a wallet for a specific blockchain chain",
    response_model=BalanceResponse,
    responses={
        200: {
            "description": "Balance retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "chain": "ETH",
                        "wallet": "0x1234...abcd",
                        "balance": 12.34,
                    }
                }
            },
        },
        500: {
            "description": "Failed to check balance",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to connect to RPC URL",
                    }
                }
            },
        },
    },
)
async def get_wallet_balance(
    chain: str = Query(..., description="Blockchain chain: eth, bsc, bnb, sol, trx"),
    wallet: str = Query(..., description="Wallet address to check balance"),
    rpc_url: str = Query(..., description="RPC URL for mainnet or testnet"),
):
    """
    Check wallet balance per blockchain chain.
    User must provide the RPC URL (mainnet or testnet).
    """
    try:
        bal = await check_balance(chain, wallet, rpc_url)
        logger.info(f"🔹 Balance checked: {wallet} on {chain.upper()} = {bal}")
        return {
            "status": "success",
            "chain": chain.upper(),
            "wallet": wallet,
            "balance": bal,
        }
    except Exception as e:
        logger.error(f"❌ Failed to check balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
