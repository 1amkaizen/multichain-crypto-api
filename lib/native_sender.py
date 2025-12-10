# 📍 lib/native_sender.py
import logging
import inspect
from lib.solana_helper import send_sol
from lib.bnb_helper import send_bnb
from lib.eth_helper import send_eth
from lib.base_helper import send_base
from lib.polygon_helper import send_polygon
from lib.trx_helper import send_trx  # ✅ import TRX helper

logger = logging.getLogger(__name__)

# Mapping helper hanya untuk native token
TOKEN_HELPERS = {
    "sol": send_sol,
    "bnb": send_bnb,
    "eth": send_eth,
    "base": send_base,
    "polygon": send_polygon,
    "trx": send_trx,  # ✅ tambah TRX
}


async def send_token(
    token: str,
    destination_wallet: str,
    amount: float,
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
            if token_lower == "trx":
                tx_hash = await send_func(
                    destination_wallet=destination_wallet,
                    amount=amount,  # sesuaikan parameter TRX juga jadi 'amount'
                    rpc_url=rpc_url,
                    private_key=private_key,
                )
            else:
                tx_hash = await send_func(
                    destination_wallet=destination_wallet,
                    amount=amount,  # cukup pakai 'amount'
                    rpc_url=rpc_url,
                    private_key=private_key,
                )

        else:
            tx_hash = send_func(
                destination_wallet=destination_wallet,
                amount=amount,
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


