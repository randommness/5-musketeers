import logging
import time
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

_cache: dict = {}
CACHE_TTL_SECONDS = 1800

def list_all_promotions(db: Session):
    cached = _cache.get("all_promotions")
    if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
        logger.debug("Cache hit for promotions")
        return cached["result"]

    result: Any = db.execute(text("SELECT * FROM public.promotion")).fetchall()
    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d promotions", len(rows))

    _cache["all_promotions"] = {"result": rows, "cached_at": time.time()}
    return rows


def list_all_shops(db: Session):
    cached = _cache.get("all_shops")
    if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
        logger.debug("Cache hit for shops")
        return cached["result"]

    result: Any = db.execute(text("SELECT * FROM public.pet_shop")).fetchall()
    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d shops", len(rows))

    _cache["all_shops"] = {"result": rows, "cached_at": time.time()}
    return rows

def list_products(db: Session, product_id: Optional[str] = None):
    # Cache key differs depending on whether filtering by a specific product or returning all
    cache_key = f"product:{product_id}" if product_id else "all_products"

    cached = _cache.get(cache_key)
    if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
        logger.debug("Cache hit for '%s' — returning %d cached product(s)", cache_key, len(cached["result"]))
        return cached["result"]

    logger.debug("Cache miss for '%s' — querying DB", cache_key)

    base_query = """
        SELECT product_id,
               product_name,
               product_category,
               pet_type,
               brand,
               product_description,
               CONCAT(unit_price, ' ', currency) AS price_per_unit,
               CONCAT(product_weight, ' ', weight_unit) AS weight_per_unit,
               packaging_type,
               product_size,
               product_rating,
               number_of_reviews,
               product_expiry_date,
               subscription_availability
        FROM public.product_info
    """

    if product_id:
        result: Any = db.execute(
            text(base_query + "WHERE product_id = :product_id ORDER BY product_id ASC;"),
            {"product_id": product_id}
        ).fetchall()
    else:
        result = db.execute(
            text(base_query + "ORDER BY product_id ASC;")
        ).fetchall()

    rows = [dict(row._mapping) for row in result]

    if not rows and product_id:
        logger.warning("No product found for product_id '%s'", product_id)
    else:
        logger.debug("SQL returned %d product(s) for '%s'", len(rows), cache_key)

    _cache[cache_key] = {"result": rows, "cached_at": time.time()}
    return rows