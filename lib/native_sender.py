# 📍 lib/native_sender.py
import logging
import inspect
from lib.solana_helper import send_sol
from lib.bnb_helper import send_bnb
from lib.eth_helper import send_eth
from lib.base_helper import send_base

logger = logging.getLogger(__name__)

# Mapping helper hanya untuk native token
TOKEN_HELPERS = {
    "sol": send_sol,
    "bnb": send_bnb,
    "eth": send_eth,  # native ETH
    "base": send_base,
}


async def send_token(
    token: str,
    destination_wallet: str,
    amount: float,
    order_id=None,
    user_id=None,
    username=None,
    full_name=None,
    rpc_url: str = None,
    private_key: str = None,
):
    """
    Kirim native token ke wallet tujuan.
    Semua native token pakai rpc_url & private_key dari endpoint
    """
    token_lower = token.lower()
    send_func = TOKEN_HELPERS.get(token_lower)

    if not send_func:
        logger.error(f"❌ Token {token} belum didukung!")
        return None

    try:
        # semua helper dianggap async
        if inspect.iscoroutinefunction(send_func):
            if token_lower == "eth":
                tx_hash = await send_func(
                    destination_wallet,
                    amount,
                    order_id,
                    user_id,
                    username,
                    full_name,
                    rpc_url=rpc_url,
                    private_key=private_key,
                )
            else:
                tx_hash = await send_func(
                    destination_wallet,
                    amount,
                    rpc_url=rpc_url,
                    private_key=private_key,
                )
        else:
            # untuk safety, sync helper juga harus dikirim param
            tx_hash = send_func(
                destination_wallet,
                amount,
                rpc_url=rpc_url,
                private_key=private_key,
            )

        if tx_hash:
            logger.info(
                f"✅ {token.upper()} berhasil dikirim ke {destination_wallet}, tx: {tx_hash}"
            )
        return tx_hash

    except Exception as e:
        logger.error(
            f"❌ Gagal kirim {token.upper()} ke {destination_wallet}: {e}",
            exc_info=True,
        )
        return None


# -------------------------------------------------------------------
# ✔ UPDATE estimate_gas_fee — TIDAK perlu destination_wallet lagi
# -------------------------------------------------------------------


async def estimate_gas_fee(token: str, chain: str, amount: float):
    """
    Estimate biaya gas untuk kirim native token.
    Tidak perlu wallet, cukup token, chain, dan amount.
    Implementasi dasar, bisa diganti sesuai chain masing-masing.
    """
    logger.info(f"🔧 Estimasi gas | token={token}, chain={chain}, amount={amount}")

    token_lower = token.lower()
    if token_lower not in TOKEN_HELPERS.keys():
        raise ValueError(f"Token {token} belum didukung untuk estimate gas")

    # contoh dummy gas fee
    gas_fee = 0.001

    logger.info(
        f"💡 Estimasi gas fee untuk {token.upper()} di chain {chain}: {gas_fee}"
    )
    return gas_fee
