# 📍 main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

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
    title="Crypto API Service",
    description="API for sending, simulating swaps, and checking crypto tokens (ETH, USDT, BNB, SOL, etc.).",
    version="1.1.1",
)

# ====================== CORS (RapidAPI Test Support) ======================
origins = [
    "https://rapidapi.com",
    "https://api.rapidapi.com",
    "*"  # sementara untuk testing semua origin
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

