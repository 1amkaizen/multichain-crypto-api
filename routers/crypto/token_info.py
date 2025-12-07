# 📍 routers/crypto/token_info.py
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

token_info_router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Response Models =====
class TokenMetadata(BaseModel):
    name: str | None
    symbol: str | None
    decimals: int | None
    contract_address: str | None
    coingecko_id: str | None


class TokenInfoResponse(BaseModel):
    status: str
    token: str
    metadata: TokenMetadata

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "token": "sol",
                "metadata": {
                    "name": "Solana",
                    "symbol": "SOL",
                    "decimals": 9,
                    "contract_address": None,
                    "coingecko_id": "solana",
                },
            }
        }


class ErrorResponse(BaseModel):
    status: str
    detail: str

    class Config:
        schema_extra = {
            "example": {"status": "error", "detail": "Token not found on CoinGecko"}
        }


# 🔹 Mapping popular token aliases to CoinGecko ID
TOKEN_ALIAS = {
    "eth": "ethereum",
    "weth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "busd": "binance-usd",
    "usdt": "tether",
    "usdc": "usd-coin",
    "trx": "tron",
    "ton": "the-open-network",
    "ada": "cardano",
    "dot": "polkadot",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "ltc": "litecoin",
    "btc": "bitcoin",
    "atom": "cosmos",
    "dai": "dai",
    "ftm": "fantom",
    "cake": "pancakeswap-token",
}


async def fetch_token_metadata_coingecko(token_id: str) -> dict:
    url = f"https://api.coingecko.com/api/v3/coins/{token_id.lower()}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=404, detail=f"Token {token_id} not found on CoinGecko"
            )
        data = resp.json()
        metadata = {
            "name": data.get("name"),
            "symbol": data.get("symbol").upper() if data.get("symbol") else None,
            "decimals": (
                data.get("detail_platforms", {})
                .get("ethereum", {})
                .get("decimal_place")
                if "detail_platforms" in data
                else None
            ),
            "contract_address": (
                data.get("detail_platforms", {})
                .get("ethereum", {})
                .get("contract_address")
                if "detail_platforms" in data
                else None
            ),
            "coingecko_id": data.get("id"),
        }
        return metadata


@token_info_router.get(
    "/token_info",
    summary="Get Token Metadata",
    description=(
        "Fetch real-time metadata of a token from CoinGecko. "
        "Popular aliases are supported, e.g., sol -> solana, eth -> ethereum, etc."
    ),
    response_model=TokenInfoResponse,
    responses={
        200: {
            "description": "Token metadata fetched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "token": "sol",
                        "metadata": {
                            "name": "Solana",
                            "symbol": "SOL",
                            "decimals": 9,
                            "contract_address": None,
                            "coingecko_id": "solana",
                        },
                    }
                }
            },
        },
        404: {
            "description": "Token not found",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Token not found on CoinGecko",
                    }
                }
            },
        },
        500: {
            "description": "Failed to fetch token metadata",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "detail": "Failed to fetch token info",
                    }
                }
            },
        },
    },
)
async def get_token_info(
    token: str = Query(..., description="Token symbol or alias to fetch metadata for")
):
    try:
        token_id = TOKEN_ALIAS.get(token.lower(), token.lower())
        metadata = await fetch_token_metadata_coingecko(token_id)
        logger.info(f"Token info fetched from CoinGecko: {token} -> {token_id}")
        return {"status": "success", "token": token.lower(), "metadata": metadata}
    except HTTPException as he:
        logger.warning(f"Token {token} not found: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"❌ Failed to fetch token info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
