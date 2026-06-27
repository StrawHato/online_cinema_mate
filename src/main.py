from fastapi import FastAPI

from src.routes import (
    accounts_router,
    profile_router,
    movies_router,
    genres_router,
    actors_router,
    cart_router,
    order_router,
)

app = FastAPI(
    title="Online Cinema Mate",
    description="A FastApi application for purchasing and watching movies online.",
)

api_version_prefix = "/api/v1"

app.include_router(accounts_router, prefix=f"{api_version_prefix}")
app.include_router(profile_router, prefix=f"{api_version_prefix}")
app.include_router(movies_router, prefix=f"{api_version_prefix}")
app.include_router(genres_router, prefix=f"{api_version_prefix}")
app.include_router(actors_router, prefix=f"{api_version_prefix}")
app.include_router(cart_router, prefix=f"{api_version_prefix}")
app.include_router(order_router, prefix=f"{api_version_prefix}")
