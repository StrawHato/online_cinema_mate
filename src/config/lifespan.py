from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    yield

    await app.state.redis.aclose()
