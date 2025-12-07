# 📍 lib/helpers/usdt/trx.py

import logging
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.exceptions import TransactionNotFound

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# ABI TRC20 standar
TRC20_ABI = [
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
    """
    Cek saldo USDT (TRC20) dari wallet_address
    """
    try:
        client = Tron(HTTPProvider(rpc_url))
        contract = client.get_contract(token_address)

        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        balance_raw = contract.functions.balanceOf(wallet_address)
        balance = balance_raw / (10**decimals)

        logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDT: {e}", exc_info=True)
        return 0.0


async def send_usdt_trx(
    destination_wallet: str,
    amount: float,
    rpc_url: str,
    private_key: str,
    token_address: str,
):
    """
    Kirim USDT TRC20 ke wallet tujuan
    """
    try:
        client = Tron(HTTPProvider(rpc_url))
        account = PrivateKey(bytes.fromhex(private_key))
        sender_address = account.public_key.to_base58check_address()

        contract = client.get_contract(token_address)

        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        value = int(amount * (10**decimals))

        # Cek saldo admin
        admin_balance = get_usdt_balance(sender_address, rpc_url, token_address)
        if admin_balance < amount:
            raise Exception(f"Saldo USDT admin tidak cukup: {admin_balance} < {amount}")

        # Cek TRX untuk energy
        admin_trx_balance = client.get_account(sender_address)["balance"] / 1_000_000
        if admin_trx_balance < 0.1:
            raise Exception(
                f"Saldo TRX admin terlalu rendah untuk bayar fee: {admin_trx_balance} TRX"
            )

        # Build & sign transaksi
        txn = (
            contract.functions.transfer(destination_wallet, value)
            .with_owner(sender_address)
            .build()
            .sign(account)
        )

        tx_result = txn.broadcast()
        tx_hash = tx_result["txid"]
        logger.info(f"🕓 Menunggu konfirmasi transaksi TRX {tx_hash}...")

        # Retry cek transaksi
        receipt = None
        for i in range(10):
            try:
                receipt = client.get_transaction_info(tx_hash)
                break
            except TransactionNotFound:
                logger.info(
                    f"⏳ Transaksi {tx_hash} belum masuk block, retry {i+1}/10..."
                )
                time.sleep(3)

        if not receipt:
            logger.error(f"❌ Transaksi {tx_hash} tidak ditemukan setelah 30 detik")
            return None

        if receipt.get("receipt", {}).get("result") == "SUCCESS":
            logger.info(
                f"✅ USDT berhasil dikirim ke {destination_wallet}, tx_hash={tx_hash}"
            )
            # log saldo sebelum & sesudah
            get_usdt_balance(sender_address, rpc_url, token_address)
            get_usdt_balance(destination_wallet, rpc_url, token_address)
            return tx_hash
        else:
            err_msg = receipt.get("receipt", {}).get("resultMessage", "Unknown error")
            logger.error(
                f"❌ Transaksi gagal: {tx_hash}, reason={err_msg}, full_receipt={receipt}"
            )
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT TRX: {e}", exc_info=True)
        return None
