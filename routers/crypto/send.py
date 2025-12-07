# 📍 routers/crypto/send.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from lib.native_sender import send_token
from lib.stable_sender import send_usdc_token, send_usdt_token

send_router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Response Models =====
class SendResponse(BaseModel):
    status: str
    tx_hash: str
    message: str


class ErrorResponse(BaseModel):
    status: str
    detail: str


# -------------------- NATIVE --------------------
@send_router.post(
    "/send/native",
    summary="Send Native Token",
    description="Endpoint to send native tokens like SOL, ETH, BNB, or BASE",
    response_model=SendResponse,
    responses={
        200: {
            "description": "Token berhasil dikirim",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "tx_hash": "5NfL1yS5kJjKx9rR4v8Q7P1M2Zq3vT6Y",
                        "message": "SOL berhasil dikirim",
                    }
                }
            },
        },
        400: {
            "description": "Transaksi gagal / validation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Transaksi gagal dijalankan",
                    }
                }
            },
        },
    },
)
async def send_native_token(
    token: str,
    destination_wallet: str,
    amount: float,
    rpc_url: str = None,
    private_key: str = None,
):
    try:
        if amount <= 0:
            raise ValueError("Amount harus lebih dari 0")

        logger.info(
            f"🚀 Permintaan kirim {token.upper()} ke {destination_wallet} sejumlah {amount}"
        )

        tx_hash = await send_token(
            token, destination_wallet, amount, rpc_url=rpc_url, private_key=private_key
        )
        if not tx_hash:
            raise HTTPException(status_code=400, detail="Transaksi gagal dijalankan")

        return {
            "status": "success",
            "tx_hash": str(tx_hash),
            "message": f"{token.upper()} berhasil dikirim",
        }

    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Gagal kirim token: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# -------------------- USDC --------------------
@send_router.post(
    "/send/usdc",
    summary="Send USDC",
    description="Endpoint to send USDC to a destination wallet via ETH/BSC/TRX chains",
    response_model=SendResponse,
    responses={
        200: {
            "description": "USDC berhasil dikirim",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "tx_hash": "3AbC9kLmN2pQ7xY8Z1D5T6V4R0W8X9Y1",
                        "message": "USDC berhasil dikirim",
                    }
                }
            },
        },
        400: {
            "description": "Transaksi gagal / validation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Transaksi gagal dijalankan",
                    }
                }
            },
        },
    },
)
async def send_usdc_endpoint(
    chain: str,
    destination_wallet: str,
    amount: float,
    token_address: str,
    rpc_url: str = None,
    private_key: str = None,
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount harus lebih dari 0")
    if not token_address:
        raise HTTPException(status_code=400, detail="USDC token address wajib diisi")

    try:
        logger.info(
            f"🚀 Permintaan kirim {amount} USDC ke {destination_wallet} via {chain.upper()}, contract={token_address}"
        )
        tx_hash = await send_usdc_token(
            destination_wallet=destination_wallet,
            amount=amount,
            chain=chain,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
        if not tx_hash:
            raise HTTPException(status_code=400, detail="Transaksi gagal dijalankan")
        return {
            "status": "success",
            "tx_hash": str(tx_hash),
            "message": "USDC berhasil dikirim",
        }
    except Exception as e:
        logger.error(f"❌ Gagal kirim USDC: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# -------------------- USDT --------------------
@send_router.post(
    "/send/usdt",
    summary="Send USDT",
    description="Endpoint to send USDT to a destination wallet via ETH/BSC/TRX chains",
    response_model=SendResponse,
    responses={
        200: {
            "description": "USDT berhasil dikirim",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "tx_hash": "7YzW1X9Q4V5T3B2N8K1L6M0P2J7H9R3A",
                        "message": "USDT berhasil dikirim",
                    }
                }
            },
        },
        400: {
            "description": "Transaksi gagal / validation error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Transaksi gagal dijalankan",
                    }
                }
            },
        },
    },
)
async def send_usdt_endpoint(
    chain: str,
    destination_wallet: str,
    amount: float,
    token_address: str,
    rpc_url: str = None,
    private_key: str = None,
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount harus lebih dari 0")
    if not token_address:
        raise HTTPException(status_code=400, detail="USDT token address wajib diisi")

    try:
        logger.info(
            f"🚀 Permintaan kirim {amount} USDT ke {destination_wallet} via {chain.upper()}, contract={token_address}"
        )
        tx_hash = await send_usdt_token(
            destination_wallet=destination_wallet,
            amount=amount,
            chain=chain,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
        if not tx_hash:
            raise HTTPException(status_code=400, detail="Transaksi gagal dijalankan")
        return {
            "status": "success",
            "tx_hash": str(tx_hash),
            "message": "USDT berhasil dikirim",
        }
    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
