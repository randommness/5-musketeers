import logging
import time
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Single cache dict — keyed by function name since there are no per-user/per-product variants
_cache: dict = {}
CACHE_TTL_SECONDS = 1800


def _is_fresh(key: str) -> bool:
    # Return True if a valid, unexpired cache entry exists for key.
    entry = _cache.get(key)
    return entry is not None and (time.time() - entry["cached_at"]) < CACHE_TTL_SECONDS


def get_all_categories(db: Session):
    if _is_fresh("categories"):
        logger.debug("Cache hit for product categories")
        return _cache["categories"]["result"]

    result: Any = db.execute(
        text("SELECT DISTINCT(product_category) FROM public.product_info")
    ).fetchall()

    categories = [row[0] for row in result]
    logger.debug("SQL returned %d product categories", len(categories))

    _cache["categories"] = {"result": categories, "cached_at": time.time()}
    return categories


def get_all_brands(db: Session):
    if _is_fresh("brands"):
        logger.debug("Cache hit for product brands")
        return _cache["brands"]["result"]

    result: Any = db.execute(
        text("SELECT DISTINCT(brand) FROM public.product_info")
    ).fetchall()

    brands = [row[0] for row in result]
    logger.debug("SQL returned %d product brands", len(brands))

    _cache["brands"] = {"result": brands, "cached_at": time.time()}
    return brands


def get_all_pet_types(db: Session):
    if _is_fresh("pet_types"):
        logger.debug("Cache hit for pet types")
        return _cache["pet_types"]["result"]

    result: Any = db.execute(
        text("SELECT DISTINCT(pet_type) FROM public.product_info")
    ).fetchall()

    pet_types = [row[0] for row in result]
    logger.debug("SQL returned %d pet types", len(pet_types))

    _cache["pet_types"] = {"result": pet_types, "cached_at": time.time()}
    return pet_types