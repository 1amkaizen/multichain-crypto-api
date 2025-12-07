# 📍 lib/stable_sender.py
import logging
from lib.usdt_helper import send_usdt
from lib.usdc_helper import send_usdc

logger = logging.getLogger(__name__)


# -------------------- Fungsi kirim USDT --------------------
async def send_usdt_token(
    destination_wallet: str,
    amount: float,
    chain: str,
    rpc_url: str = None,
    private_key: str = None,
    token_address: str = None,  # ✅ tambahkan
):
    """
    Kirim USDT ke wallet tujuan sesuai chain
    """
    try:
        tx_hash = await send_usdt(
            destination_wallet,
            amount,
            chain.lower(),
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,  # diteruskan ke helper
        )
        logger.info(
            f"✅ USDT berhasil dikirim ke {destination_wallet} di chain {chain.upper()}, tx: {tx_hash}"
        )
        return tx_hash
    except Exception as e:
        logger.error(
            f"❌ Gagal kirim USDT ke {destination_wallet} di chain {chain.upper()}: {e}",
            exc_info=True,
        )
        return None


# -------------------- Fungsi kirim USDC --------------------
async def send_usdc_token(
    destination_wallet: str,
    amount: float,
    chain: str,
    rpc_url: str = None,
    private_key: str = None,
    token_address: str = None,  # ✅ tambahkan
):
    """
    Kirim USDC ke wallet tujuan sesuai chain
    """
    if not token_address:
        raise ValueError("USDC token_address wajib diisi")

    try:
        tx_hash = await send_usdc(
            destination_wallet,
            amount,
            chain.lower(),
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,  # diteruskan ke helper
        )
        logger.info(
            f"✅ USDC berhasil dikirim ke {destination_wallet} di chain {chain.upper()}, tx: {tx_hash}"
        )
        return tx_hash
    except Exception as e:
        logger.error(
            f"❌ Gagal kirim USDC ke {destination_wallet} di chain {chain.upper()}: {e}",
            exc_info=True,
        )
        return None


