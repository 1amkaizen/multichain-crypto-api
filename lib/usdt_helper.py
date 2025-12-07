# 📍 lib/usdt_helper.py
import logging
from lib.helpers.usdt.eth import send_usdt_eth
from lib.helpers.usdt.bsc import send_usdt_bsc
from lib.helpers.usdt.trx import send_usdt_trx
from lib.helpers.usdt.base import send_usdt_base
from lib.helpers.usdt.sol import send_usdt_solana
import asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(name)s: %(message)s",
)


async def send_usdt(
    destination_wallet: str,
    amount: float,
    chain: str,
    rpc_url: str = None,
    private_key: str = None,
    token_address: str = None,  # ✅ tambahkan ini
):
    """
    Router universal untuk kirim USDT di berbagai chain.
    rpc_url, private_key, token_address bisa di-override dari endpoint.
    """
    chain = chain.lower()

    if chain == "eth":
        return await send_usdt_eth(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "bsc":
        return await send_usdt_bsc(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "trx":
        return await send_usdt_trx(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "base":
        return await send_usdt_base(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "sol":
        # pakai loop.run_in_executor biar synchronous jadi awaitable
        return await asyncio.get_running_loop().run_in_executor(
            None,
            send_usdt_solana,
            destination_wallet,
            amount,
            rpc_url,
            private_key,
            token_address,
        )
    else:
        raise ValueError(f"Chain {chain} tidak didukung untuk USDT!")
