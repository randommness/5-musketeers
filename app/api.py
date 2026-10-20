import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, first_check_in, goal_achiever, products, product_pair
from app.routers import api_catalog, api_login, api_customer_dashboard, api_retail, api_new_order, api_new_review, api_update_order

def create_app() -> FastAPI:
    app = FastAPI(title="Customer data & insights API")

    # Read allowed origins from env — comma-separated list of frontend URLs.
    # Default to local if none set
    raw = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")
    allowed_origins = [origin.strip() for origin in raw.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], #allowed_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(first_check_in.router)
    app.include_router(goal_achiever.router)
    app.include_router(products.router)
    app.include_router(product_pair.router)

    app.include_router(api_catalog.router)
    app.include_router(api_login.router)
    app.include_router(api_customer_dashboard.router)
    app.include_router(api_retail.router)
    app.include_router(api_new_order.router)
    app.include_router(api_new_review.router)
    app.include_router(api_update_order.router)
    
    return app