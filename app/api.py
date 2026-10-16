import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import first_check_in, goal_achiever

def create_app() -> FastAPI:
    app = FastAPI(title="Customer data & insights API")

    # Read allowed origins from env — comma-separated list of frontend URLs.
    # Default to local if none set
    raw = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000/")
    allowed_origins = [origin.strip() for origin in raw.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(first_check_in.router)
    app.include_router(goal_achiever.router)

    return app
