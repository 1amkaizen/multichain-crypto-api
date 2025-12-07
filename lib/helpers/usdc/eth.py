# 📍 lib/helpers/usdc/eth.py
import logging
import asyncio
from web3 import Web3

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# ===== ERC20 ABI =====
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]


# ===== Fungsi cek saldo USDC =====
def get_usdc_balance(wallet_address: str, rpc_url: str, token_address: str) -> float:
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("RPC tidak terhubung")
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6
        balance = contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call() / (10**decimals)
        logger.info(f"💰 Saldo USDC {wallet_address}: {balance} USDC")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDC: {e}", exc_info=True)
        return 0.0


# ===== Async polling untuk receipt =====
async def wait_tx_receipt_async(
    w3: Web3, tx_hash: str, poll_interval: int = 5, timeout: int = 180
):
    await asyncio.sleep(2)  # delay awal supaya node register tx
    start = asyncio.get_event_loop().time()
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except Exception as e:
            if "not found" not in str(e):
                raise
        if asyncio.get_event_loop().time() - start > timeout:
            raise TimeoutError(f"⏳ Timeout tunggu receipt tx {tx_hash}")
        await asyncio.sleep(poll_interval)


# ===== Fungsi Kirim USDC ERC20 =====
async def send_usdc_eth(
    destination_wallet: str,
    amount: float,
    rpc_url: str,
    private_key: str,
    token_address: str,
    chain_id: int = None,  # opsional, bisa mainnet/testnet
):
    try:
        if not rpc_url or not private_key or not token_address:
            raise Exception("RPC, private_key, dan token_address wajib diisi")

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("RPC tidak terhubung")

        # Tentukan chain_id otomatis dari RPC jika tidak dikirim
        if chain_id is None:
            rpc_lower = rpc_url.lower()
            if "goerli" in rpc_lower:
                chain_id = 5
            elif "sepolia" in rpc_lower:
                chain_id = 11155111
            elif "bsc-test" in rpc_lower:
                chain_id = 97
            elif "bsc" in rpc_lower:
                chain_id = 56
            else:
                chain_id = 1  # default mainnet

        account = w3.eth.account.from_key(private_key)
        from_address = Web3.to_checksum_address(account.address)
        destination_wallet = Web3.to_checksum_address(destination_wallet)
        token_address = Web3.to_checksum_address(token_address)

        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6

        # log saldo sebelum kirim
        get_usdc_balance(from_address, rpc_url, token_address)
        get_usdc_balance(destination_wallet, rpc_url, token_address)

        # cek balance cukup
        balance_usdc = contract.functions.balanceOf(from_address).call() / (
            10**decimals
        )
        if amount > balance_usdc:
            raise Exception(f"USDC balance tidak cukup: {balance_usdc} < {amount}")

        value = int(amount * (10**decimals))
        nonce = w3.eth.get_transaction_count(from_address, "pending")

        tx = contract.functions.transfer(destination_wallet, value).build_transaction(
            {
                "chainId": chain_id,
                "gas": 100000,
                "gasPrice": int(w3.eth.gas_price * 1.2),
                "nonce": nonce,
                "from": from_address,
            }
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        receipt = await wait_tx_receipt_async(w3, tx_hash.hex())
        if receipt.status == 1:
            logger.info(
                f"✅ USDC ERC20 berhasil masuk ke {destination_wallet}, tx_hash={tx_hash.hex()}"
            )
            get_usdc_balance(from_address, rpc_url, token_address)
            get_usdc_balance(destination_wallet, rpc_url, token_address)
            return tx_hash.hex()
        else:
            logger.error(f"❌ Transaksi gagal masuk blockchain: {tx_hash.hex()}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDC ERC20: {e}", exc_info=True)
        return None
