# 📍 lib/helpers/usdt/base.py

import logging
import time
import asyncio
from functools import partial
from web3 import Web3

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# ERC20 ABI minimal
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


def get_usdt_balance(wallet_address: str, rpc_url: str, token_address: str) -> float:
    """Cek saldo USDT Base (dinamis, mirip ETH)"""
    try:
        wallet_address = Web3.to_checksum_address(wallet_address)
        token_address = Web3.to_checksum_address(token_address.strip())
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6")
            decimals = 6

        balance_raw = contract.functions.balanceOf(wallet_address).call()
        balance = balance_raw / (10**decimals)
        logger.info(f"💰 Saldo USDT Base {wallet_address}: {balance}")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo Base USDT: {e}", exc_info=True)
        return 0.0


def send_usdt_base_sync(
    destination_wallet: str,
    amount: float,
    rpc_url: str,
    private_key: str,
    token_address: str,
):
    """Kirim USDT Base (sync, robust, dinamis)"""
    try:
        destination_wallet = Web3.to_checksum_address(destination_wallet.strip())
        token_address = Web3.to_checksum_address(token_address.strip())
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)
        from_address = Web3.to_checksum_address(account.address)
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6")
            decimals = 6

        value = int(amount * (10**decimals))
        nonce = w3.eth.get_transaction_count(from_address, "pending")
        safe_gas_price = int(w3.eth.gas_price * 1.2)

        txn = contract.functions.transfer(destination_wallet, value).build_transaction(
            {
                "from": from_address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": safe_gas_price,
                "chainId": w3.eth.chain_id,
            }
        )

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        # retry loop sampai mined atau timeout 180 detik
        receipt = None
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                break
            except Exception:
                logger.info("⏳ Transaksi belum mined, tunggu 5 detik...")
                time.sleep(5)

        if not receipt:
            logger.error(
                f"❌ Transaksi {tx_hash.hex()} tidak ditemukan dalam 180 detik"
            )
            return None

        if receipt.status == 1:
            logger.info(
                f"✅ Token berhasil dikirim ke {destination_wallet}, tx_hash={tx_hash.hex()}"
            )
            get_usdt_balance(from_address, rpc_url, token_address)
            get_usdt_balance(destination_wallet, rpc_url, token_address)
            return tx_hash.hex()
        else:
            logger.error(f"❌ Transaksi gagal: {tx_hash.hex()}, receipt={receipt}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT Base: {e}", exc_info=True)
        return None


async def send_usdt_base(
    destination_wallet: str,
    amount: float,
    rpc_url: str,
    private_key: str,
    token_address: str,
):
    """Kirim USDT Base (async-safe)"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        partial(
            send_usdt_base_sync,
            destination_wallet,
            amount,
            rpc_url,
            private_key,
            token_address,
        ),
    )
