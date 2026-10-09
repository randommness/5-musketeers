from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import first_check_in

def create_app() -> FastAPI:
    app = FastAPI(title="Customer data & insights API")
    
    # This allows API requests from any URL instead of blocking a fetch request
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # internal only — fine to keep open; lock down if ever exposed
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(first_check_in.router)

    return app
