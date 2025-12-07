# 📍 routers/crypto/send.py
import logging
from fastapi import APIRouter, HTTPException
from lib.native_sender import send_token
from lib.stable_sender import send_usdc_token, send_usdt_token


send_router = APIRouter()
logger = logging.getLogger(__name__)


@send_router.post(
    "/send/native",
    summary="Send Native Token",  # 🔹 teks yang muncul di Swagger UI / Redoc
    description="Endpoint to send native tokens like SOL, ETH, BNB, or BASE to a destination wallet",
)

async def send_native_token(
    token: str,
    destination_wallet: str,
    amount: float,
    rpc_url: str = None,  # 🔹 user input RPC
    private_key: str = None,  # 🔹 user input private key untuk native token
):
    """Kirim native token ke wallet tujuan"""
    try:
        if amount <= 0:
            raise ValueError("Amount harus lebih dari 0")

        logger.info(
            f"🚀 Permintaan kirim {token.upper()} ke {destination_wallet} sejumlah {amount}"
        )

        # Kirim token (native token saja)
        tx_hash = await send_token(
            token,
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
        )

        if not tx_hash:
            # Kalo send_token gagal tapi ga raise exception
            raise HTTPException(
                status_code=400,
                detail=f"Transaksi gagal dijalankan. Periksa saldo atau wallet.",
            )

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
)

async def send_usdc_endpoint(
    chain: str,  # misal: eth, bsc, trx
    destination_wallet: str,
    amount: float,
    token_address: str,  # ✅ USDC contract address
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
            token_address=token_address,  # ✅ kirim contract dari endpoint
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
)

async def send_usdt_endpoint(
    chain: str,  # misal: eth, bsc, trx
    destination_wallet: str,
    amount: float,
    token_address: str,  # ✅ USDT contract address
    rpc_url: str = None,
    private_key: str = None,
):
    """Kirim USDT ke wallet tujuan"""
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
