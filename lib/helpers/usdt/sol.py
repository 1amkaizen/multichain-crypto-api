# 📍 lib/helpers/usdt/sol.py
import logging
import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    transfer_checked,
    create_associated_token_account,
    get_associated_token_address,
    TransferCheckedParams,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def get_client(rpc_url: str) -> Client:
    """Inisialisasi Solana RPC client"""
    return Client(rpc_url)


def load_keypair(secret_key_base58: str) -> Keypair:
    """Load keypair dari base58 string"""
    key_bytes = base58.b58decode(secret_key_base58)
    if len(key_bytes) == 32:
        return Keypair.from_secret_key(key_bytes)
    elif len(key_bytes) == 64:
        return Keypair.from_bytes(key_bytes)
    else:
        raise ValueError(
            f"❌ Private key salah, panjang {len(key_bytes)} bukan 32/64 bytes"
        )


def get_or_create_ata(client: Client, owner_pub: Pubkey, mint_pub: Pubkey, payer: Keypair) -> Pubkey:
    """Cek atau buat Associated Token Account (ATA)"""
    token_account = get_associated_token_address(owner_pub, mint_pub)
    resp = client.get_account_info(token_account)
    if resp.value is None:
        logger.info(f"⚠️ ATA belum ada, membuat untuk {owner_pub}")
        tx = Transaction.new_signed_with_payer(
            [create_associated_token_account(payer=payer.pubkey(), owner=owner_pub, mint=mint_pub)],
            payer=payer.pubkey(),
            signing_keypairs=[payer],
            recent_blockhash=client.get_latest_blockhash().value.blockhash,
        )
        sig = send_tx(client, tx, payer)
        logger.info(f"✅ ATA dibuat untuk {owner_pub}, sig={sig}")
    return token_account


def get_usdt_balance(client: Client, wallet_address: str, usdt_mint_address: str) -> float:
    """Cek saldo USDT SPL di wallet tertentu"""
    try:
        owner_pub = Pubkey.from_string(wallet_address)
        mint_pub = Pubkey.from_string(usdt_mint_address)
        token_account = get_associated_token_address(owner_pub, mint_pub)
        resp = client.get_account_info(token_account)
        if resp.value is None:
            logger.info(f"ℹ️ ATA belum ada untuk {wallet_address}, saldo = 0")
            return 0.0

        bal_resp = client.get_token_account_balance(token_account)
        balance_raw = int(bal_resp.value.amount)
        decimals = int(bal_resp.value.decimals)
        balance = balance_raw / (10 ** decimals)
        logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDT: {e}", exc_info=True)
        return 0.0


def send_tx(client: Client, tx: Transaction, signer: Keypair) -> str:
    """Helper untuk kirim transaction, return string signature"""
    raw_txn = bytes(tx)
    resp = client.send_raw_transaction(
        raw_txn, opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed")
    )
    signature = getattr(resp, "value", None)
    if signature is not None and hasattr(signature, "to_string"):
        return signature.to_string()
    return str(signature)


def send_usdt_solana(
    destination_wallet: str,
    amount: float,
    rpc_url: str,
    secret_key_base58: str,
    usdt_mint_address: str,
):
    """Kirim USDT SPL ke wallet tujuan (RPC, key, mint lewat param)"""
    try:
        client = get_client(rpc_url)
        admin_keypair = load_keypair(secret_key_base58)

        if destination_wallet == str(admin_keypair.pubkey()):
            logger.warning(f"❌ Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")
            return None

        mint_pub = Pubkey.from_string(usdt_mint_address)
        dest_pub = Pubkey.from_string(destination_wallet)
        decimals = 6
        amount_int = int(amount * (10 ** decimals))

        # Pastikan ATA sender & receiver ada
        sender_ata = get_or_create_ata(client, admin_keypair.pubkey(), mint_pub, admin_keypair)
        dest_ata = get_or_create_ata(client, dest_pub, mint_pub, admin_keypair)

        # Cek saldo
        sender_balance = get_usdt_balance(client, str(admin_keypair.pubkey()), usdt_mint_address)
        if sender_balance < amount:
            logger.error(f"❌ Saldo USDT tidak cukup! Diminta: {amount}, tersedia: {sender_balance}")
            return None

        logger.info(f"🔹 Sender ATA: {sender_ata}, Receiver ATA: {dest_ata}, Amount: {amount} USDT ({amount_int} units)")

        # Buat transaksi transfer pakai new_signed_with_payer
        tx_transfer = Transaction.new_signed_with_payer(
            [transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=sender_ata,
                    mint=mint_pub,
                    dest=dest_ata,
                    owner=admin_keypair.pubkey(),
                    amount=amount_int,
                    decimals=decimals,
                )
            )],
            payer=admin_keypair.pubkey(),
            signing_keypairs=[admin_keypair],
            recent_blockhash=client.get_latest_blockhash().value.blockhash,
        )

        sig = send_tx(client, tx_transfer, admin_keypair)
        logger.info(f"✅ USDT SOL berhasil dikirim ke {destination_wallet}, sig={sig}")
        return sig

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT SOL: {e}", exc_info=True)
        return None
