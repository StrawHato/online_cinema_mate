from fastapi import FastAPI

from src.routes import accounts_router

app = FastAPI(
    title="Online Cinema Mate",
    description="A FastApi application for purchasing and watching movies online.",
)

api_version_prefix = "/api/v1"

app.include_router(accounts_router, prefix=f"{api_version_prefix}/")
