# 📍 lib/usdc_helper.py
import logging
import asyncio
from lib.helpers.usdc.eth import send_usdc_eth
from lib.helpers.usdc.bsc import send_usdc_bsc
from lib.helpers.usdc.trx import send_usdc_trx
from lib.helpers.usdc.base import send_usdc_base
from lib.helpers.usdc.sol import send_usdc_solana


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


async def send_usdc(
    destination_wallet: str,
    amount: float,
    chain: str,
    rpc_url: str = None,
    private_key: str = None,
    token_address: str = None,  # ✅ tambahkan ini
):
    """
    Router universal untuk kirim USDC di berbagai chain.
    rpc_url, private_key, token_address bisa di-override dari endpoint.
    """
    chain = chain.lower()

    if chain == "eth":
        return await send_usdc_eth(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "bsc":
        return await send_usdc_bsc(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "trx":
        return await send_usdc_trx(
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
            token_address=token_address,
        )
    elif chain == "base":
        return await send_usdc_base(
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
            send_usdc_solana,
            destination_wallet,
            amount,
            rpc_url,
            private_key,
            token_address,
        )
    else:
        raise ValueError(f"Chain {chain} tidak didukung untuk USDC!")
