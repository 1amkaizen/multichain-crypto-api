# 📍 main.py

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

load_dotenv()

# ====================== LOGGING ======================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ====================== LOAD ENV ======================
# 🔥 Ambil secret dari environment, bukan dari config
RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET", None)


# ====================== ROUTER CRYPTO ======================
from routers.crypto.ping import ping_router
from routers.crypto.send import send_router
from routers.crypto.balance import balance_router
from routers.crypto.price import price_router
from routers.crypto.estimate_gas import estimate_gas_router
from routers.crypto.tokens import tokens_router
from routers.crypto.swap import swap_router
from routers.crypto.token_info import token_info_router
from routers.crypto.tx_status import tx_status_router


# ====================== APP ======================
app = FastAPI(
    title="MultiChain Crypto API",
    description="API for sending, simulating swaps, and checking crypto tokens (ETH, USDT, BNB, SOL, etc.).",
    version="1.1.1",
)


# ====================== MIDDLEWARE ANTI AKSES DOMAIN ASLI ======================
@app.middleware("http")
async def enforce_rapidapi_proxy(request: Request, call_next):
    """
    🔒 Middleware ini memblokir akses langsung ke domain asli,
    tapi mengizinkan akses ke /docs, /redoc, /openapi.json, dan /ping.
    """

    path = request.url.path

    # 🔓 WHITELIST → boleh diakses tanpa RapidAPI
    PUBLIC_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/crypto/ping",
        "/api/v1/crypto/tokens",
        "/api/v1/crypto/token_info",
    ]

    # kalau path ada di whitelist → langsung lolos
    if path in PUBLIC_PATHS:
        return await call_next(request)

    # selain whitelist → wajib RapidAPI
    proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret")

    if RAPIDAPI_SECRET is None:
        logger.error("❌ ENV 'RAPIDAPI_SECRET' belum diset!")
        raise HTTPException(status_code=500, detail="Server misconfigured")

    if proxy_secret != RAPIDAPI_SECRET:
        logger.warning(
            f"❌ Blok akses ilegal dari {request.client.host} ke {request.url.path}"
        )
        raise HTTPException(
            status_code=403, detail="Forbidden: Only RapidAPI gateway allowed"
        )

    logger.info(f"✅ Akses RapidAPI valid ke {path}")
    return await call_next(request)


# ====================== CORS (RapidAPI Testing) ======================
origins = [
    "https://rapidapi.com",
    "https://api.rapidapi.com",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================== REGISTER CRYPTO ROUTERS ======================
crypto_routers = [
    ping_router,
    send_router,
    balance_router,
    price_router,
    estimate_gas_router,
    tokens_router,
    swap_router,
    token_info_router,
    tx_status_router,
]

for r in crypto_routers:
    app.include_router(r, prefix="/api/v1/crypto", tags=["Crypto"])


# ====================== CUSTOM OPENAPI (HANYA CRYPTO) ======================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    crypto_routes = [
        route for route in app.routes if "Crypto" in getattr(route, "tags", [])
    ]

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=crypto_routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
