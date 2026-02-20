# 📍 lib/coingecko.py
import aiohttp
import logging
import os
import asyncio
import time
from pathlib import Path
import ujson as json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = os.getenv("COINGECKO_API", "https://api.coingecko.com/api/v3/simple/price")
CACHE_FILE = Path("data/cache_prices.json")  # file cache JSON

TOKEN_MAP = {
    "sol": "solana",
    "eth": "ethereum",
    "usdt": "tether",
    "usdc": "usd-coin",
    "bnb": "binancecoin",
    "trx": "tron",
    "ton": "the-open-network",
    "base": "base-protocol",
}

# ======= Global session & cache =======
_session = None
_price_cache = {}  # {token: (timestamp, price)}
CACHE_TTL = 15  # detik


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
        return token_data.get("price_idr")
    return None


def update_cached_price(token: str, price_idr: float):
    cache = load_json_cache()
    cache[token] = {"price_idr": price_idr, "updated_at": time.time()}
    save_json_cache(cache)


# ======= HTTP Session =======
async def _get_session():
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=5)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


# ======= Harga Token =======
async def get_current_price(token: str, retries=3, delay=1) -> float:
    """
    Ambil harga token dalam IDR
    - pakai cache memory 15 detik
    - fallback ke file JSON kalau gagal
    - terakhir fallback 0
    """
    token_lower = token.lower()
    coin_id = TOKEN_MAP.get(token_lower)
    if not coin_id:
        logger.warning(f"⚠️ Token {token} belum support")
        return 0

    now = time.time()
    # ===== cek cache memory =====
    if token_lower in _price_cache:
        ts, price = _price_cache[token_lower]
        if now - ts < CACHE_TTL:
            return price

    # ===== fetch API =====
    params = {"ids": ",".join(TOKEN_MAP.values()), "vs_currencies": "idr,usd"}
    for attempt in range(1, retries + 1):
        try:
            session = await _get_session()
            async with session.get(BASE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"❌ Attempt {attempt} gagal fetch {token}, status {resp.status}"
                    )
                    raise Exception("Status != 200")
                data = await resp.json()
                price_info = data.get(coin_id)
                if not price_info:
                    raise Exception("Token tidak ada")
                price_idr = price_info.get("idr", 0)
                price_usd = price_info.get("usd", 0)
                if price_idr == 0 or price_usd == 0:
                    raise Exception("Data harga kosong")
                kurs = price_idr / price_usd
                logger.info(
                    f"💲 Harga {token.upper()} : {price_idr:,.0f} IDR | {price_usd:.2f} USD | Kurs: {kurs:,.2f}"
                )

                # update cache memory + JSON
                _price_cache[token_lower] = (now, price_idr)
                update_cached_price(token_lower, price_idr)
                return price_idr
        except Exception as e:
            logger.warning(
                f"⚠️ Attempt {attempt} gagal untuk {token}, retry in {delay}s: {e}"
            )
            await asyncio.sleep(delay)

    # ===== fallback file JSON =====
    cached_price = get_cached_price(token_lower)
    if cached_price:
        logger.info(f"✅ Pakai harga cache JSON untuk {token}: {cached_price}")
        return cached_price

    # ===== fallback default =====
    logger.error(f"❌ Semua attempt gagal untuk {token}, fallback 0")
    return 0


# ======= Utility =======
async def log_all_prices():
    """Fetch semua harga token sekaligus secara parallel"""
    await asyncio.gather(*(get_current_price(t) for t in TOKEN_MAP.keys()))


async def get_current_sol_price() -> float:
    """Ambil harga SOL khusus IDR saja, pakai cache"""
    return await get_current_price("sol")


async def close_session():
    """Tutup session global saat shutdown bot"""
    global _session
    if _session and not _session.closed:
        await _session.close()
