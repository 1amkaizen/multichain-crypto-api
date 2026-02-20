# 📍 lib/price_mapper.py
import logging
import httpx
import asyncio
import json
from pathlib import Path
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Mapping chain/token ke CoinGecko ID
COINGECKO_IDS = {
    "sol": "solana",
    "bnb": "binancecoin",
    "trx": "tron",
    "usdt": "tether",
    "usdc": "usd-coin",
    "ton": "the-open-network",
    "base": "ethereum",
    "eth": "ethereum",
}

CACHE_FILE = Path("data/cache__map_prices.json")
CACHE_TTL = 60  # cache 1 menit


# ======= Helper JSON Cache =======
def load_json_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_json_cache(data):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data))


def get_cached_price(token: str):
    cache = load_json_cache()
    token_data = cache.get(token)
    if token_data:
        # cek TTL
        if time.time() - token_data.get("updated_at", 0) < CACHE_TTL:
            return token_data.get("price_idr")
    return None


def update_cached_price(token: str, price_idr: float):
    cache = load_json_cache()
    cache[token] = {"price_idr": price_idr, "updated_at": time.time()}
    save_json_cache(cache)


# ======= Ambil harga token =======
async def get_token_amount(chain: str, nominal_idr: int) -> float:
    """
    Ambil jumlah token dari nominal IDR:
    1. Prioritas: fetch dari Coingecko
    2. Simpan harga ke file cache
    3. Kalau gagal, ambil dari file cache
    """
    token_id = COINGECKO_IDS.get(chain.lower())
    if not token_id:
        logger.error(f"❌ Chain/token {chain} tidak dikenali")
        return 0

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=idr"

    # ===== coba fetch realtime =====
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            price_idr = data.get(token_id, {}).get("idr")
            if price_idr:
                # update cache
                update_cached_price(chain.lower(), price_idr)
                amount = nominal_idr / price_idr
                amount = round(amount, 6)
                logger.info(
                    f"💰 Nominal {nominal_idr} IDR = {amount} {chain.upper()} (harga {price_idr} IDR/{chain.upper()})"
                )
                return amount
            else:
                logger.warning(f"⚠️ Harga {chain.upper()} kosong dari API")
    except Exception as e:
        logger.warning(f"⚠️ Error ambil harga {chain.upper()} realtime: {e}")

    # ===== fallback cache =====
    cached_price = get_cached_price(chain.lower())
    if cached_price:
        amount = nominal_idr / cached_price
        amount = round(amount, 6)
        logger.info(
            f"✅ Pakai harga cache untuk {chain.upper()}: {cached_price} IDR, nominal {amount} {chain.upper()}"
        )
        return amount

    logger.error(f"❌ Semua gagal untuk {chain.upper()}, fallback 0")
    return 0


# 🔹 Tambahan: get_locked_token_amount
async def get_locked_token_amount(chain: str, nominal_idr: int) -> float:
    """
    Hitung jumlah token yang akan dikunci/locked.
    Bisa dikurangi fee atau multiplier tertentu jika mau.
    Contoh: 1% fee locked token.
    """
    base_amount = await get_token_amount(chain, nominal_idr)
    locked_amount = base_amount * 0.99  # contoh fee 1% untuk locked
    locked_amount = round(locked_amount, 6)
    logger.info(
        f"🔒 Locked token {chain.upper()}: {locked_amount} dari nominal {base_amount}"
    )
    return locked_amount
