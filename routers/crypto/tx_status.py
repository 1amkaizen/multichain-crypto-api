# 📍 routers/crypto/tx_status.py
import logging
from fastapi import APIRouter, HTTPException, Query
from solana.rpc.async_api import AsyncClient as SolanaClient
from solders.signature import Signature
from web3 import AsyncWeb3, AsyncHTTPProvider
from tronpy.async_tron import AsyncTron
import asyncio

tx_status_router = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ----------------- SOLANA -----------------
async def get_solana_tx_status(
    tx_hash: str, rpc_url: str, max_attempts: int = 15, delay: float = 2.0
):
    """Cek status transaksi Solana sampai meta muncul atau max_attempts"""
    signature = Signature.from_string(tx_hash)
    attempt = 0
    async with SolanaClient(rpc_url) as client:
        while attempt < max_attempts:
            attempt += 1
            for commitment in ["confirmed", "finalized"]:
                resp = await client.get_transaction(
                    signature, encoding="json", commitment=commitment
                )
                tx_data = resp.value
                if tx_data:
                    # ambil meta via attribute
                    meta = getattr(tx_data, "meta", None)

                    # kalau meta ada → return detail lengkap
                    if meta:
                        success = getattr(meta, "err", None) is None
                        return {
                            "status": "success" if success else "failed",
                            "tx_hash": tx_hash,
                            "slot": getattr(tx_data, "slot", None),
                            "fee": getattr(meta, "fee", None),
                            "pre_balances": getattr(meta, "pre_balances", None),
                            "post_balances": getattr(meta, "post_balances", None),
                            "err": getattr(meta, "err", None),
                        }

                    # kalau meta None tapi tx ada → treat as success sementara
                    elif hasattr(tx_data, "slot") and tx_data.slot:
                        logger.info(
                            f"Tx {tx_hash} ditemukan di slot {tx_data.slot}, meta belum tersedia, return provisional success"
                        )
                        return {
                            "status": "success",
                            "tx_hash": tx_hash,
                            "slot": tx_data.slot,
                            "note": "Tx sukses, meta belum tersedia, data lengkap menyusul",
                        }

            backoff = delay * (2 ** (attempt - 1))  # exponential backoff
            logger.info(
                f"Attempt {attempt}: tx {tx_hash} belum finalized, retry {backoff}s"
            )
            await asyncio.sleep(backoff)

    return {
        "status": "pending",
        "tx_hash": tx_hash,
        "note": "Belum confirmed setelah max attempts",
    }


# ----------------- EVM (ETH/BSC/Polygon/Base) -----------------
async def get_evm_tx_status(tx_hash: str, rpc_url: str):
    """Cek status transaksi EVM chain via RPC"""
    w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
    receipt = await w3.eth.get_transaction_receipt(tx_hash)
    if receipt is None:
        return {"status": "pending", "tx_hash": tx_hash}

    tx = await w3.eth.get_transaction(tx_hash)
    value_eth = w3.from_wei(tx.value, "ether")
    gas_price = w3.from_wei(tx.gasPrice, "gwei") if tx.gasPrice else None

    return {
        "status": "success" if receipt.status == 1 else "failed",
        "tx_hash": tx_hash,
        "from": tx["from"],
        "to": tx["to"],
        "value": float(value_eth),
        "gasUsed": receipt.gasUsed,
        "gasPriceGwei": float(gas_price) if gas_price else None,
        "cumulativeGasUsed": receipt.cumulativeGasUsed,
        "transactionIndex": receipt.transactionIndex,
        "blockNumber": receipt.blockNumber,
        "logs": [dict(log) for log in receipt.logs],
    }


# ----------------- TRON -----------------
async def get_trx_tx_status(tx_hash: str, max_attempts: int = 5, delay: float = 2.0):
    """Cek status transaksi TRX via tronpy dengan retry jika rate-limit"""
    async with AsyncTron() as client:
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                tx_info = await client.get_transaction_info(tx_hash)
                receipt = tx_info.get("receipt", {})
                result = receipt.get("result") if receipt else None
                if result == "SUCCESS":
                    status = "success"
                elif result == "FAILED":
                    status = "failed"
                else:
                    status = "pending"

                return {
                    "status": status,
                    "tx_hash": tx_hash,
                    "fee": tx_info.get("fee"),
                    "contractResult": tx_info.get("contractResult"),
                    "logs": tx_info.get("log"),
                    "blockNumber": tx_info.get("blockNumber"),
                }

            except Exception as e:
                # kalau rate-limit, delay lebih lama
                if (
                    hasattr(e, "response")
                    and e.response is not None
                    and e.response.status_code == 429
                ):
                    logger.warning(
                        f"TronGrid 429, retry {attempt}/{max_attempts} setelah delay {delay}s"
                    )
                    await asyncio.sleep(delay * attempt)  # backoff linear
                else:
                    logger.error(f"Gagal cek TRX tx {tx_hash}: {e}", exc_info=True)
                    return {"status": "pending", "tx_hash": tx_hash, "note": str(e)}

        return {
            "status": "pending",
            "tx_hash": tx_hash,
            "note": "Max retry reached, rate-limit?",
        }


# ----------------- API Endpoint -----------------
@tx_status_router.get("/tx_status", summary="Get Transaction Status")
async def get_tx_status(
    chain: str = Query(
        ..., description="Blockchain chain: eth, bnb, polygon, sol, trx, base"
    ),
    tx_hash: str = Query(..., description="Transaction hash to query the status of"),
    rpc_url: str = Query(
        None, description="RPC URL for the blockchain node (required for EVM & Solana)"
    ),
):
    chain = chain.lower()
    try:
        if chain in ["sol"]:
            if not rpc_url:
                raise HTTPException(
                    status_code=400, detail="RPC URL harus diberikan untuk Solana"
                )
            return await get_solana_tx_status(tx_hash, rpc_url)

        elif chain in ["eth", "bnb", "polygon", "base"]:
            if not rpc_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"RPC URL harus diberikan untuk {chain.upper()}",
                )
            logger.info(f"🔹 Checking {chain.upper()} tx via RPC: {tx_hash}")
            return await get_evm_tx_status(tx_hash, rpc_url)

        elif chain == "trx":
            return await get_trx_tx_status(tx_hash)

        else:
            raise HTTPException(
                status_code=400, detail=f"Chain {chain} is not supported"
            )

    except Exception as e:
        logger.error(f"❌ Failed to check tx_status [{chain}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
