import logging
import time
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Cache keyed per customer_id since results differ per user
_cache: dict = {}
CACHE_TTL_SECONDS = 1800


def _is_fresh(key: str) -> bool:
    """Return True if a valid, unexpired cache entry exists for key."""
    entry = _cache.get(key)
    return entry is not None and (time.time() - entry["cached_at"]) < CACHE_TTL_SECONDS


def get_customer_profile(customer_id: str, db: Session):
    cache_key = f"customer_profile:{customer_id}"
    if _is_fresh(cache_key):
        logger.debug("Cache hit for customer profile %s", customer_id)
        return _cache[cache_key]["result"]

    result: Any = db.execute(
        text("SELECT * FROM public.customer_info WHERE customer_id = :customer_id"),
        {"customer_id": customer_id}
    ).fetchone()

    # fetchone() returns a single row — convert to a flat dictionary
    customer_info: dict = dict(result._mapping) if result else {}
    logger.debug("SQL returned customer info for %s", customer_id)

    _cache[cache_key] = {"result": customer_info, "cached_at": time.time()}
    return customer_info


def get_customer_orders(customer_id: str, db: Session):
    cache_key = f"orders:{customer_id}"
    if _is_fresh(cache_key):
        logger.debug("Cache hit for orders %s", customer_id)
        return _cache[cache_key]["result"]

    result: Any = db.execute(
        text("SELECT * FROM public.orders WHERE customer_id = :customer_id"),
        {"customer_id": customer_id}
    ).fetchall()

    # fetchall() returns multiple rows — convert each to a dict and collect as a list (JSON array)
    orders: list[dict] = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d orders for %s", len(orders), customer_id)

    _cache[cache_key] = {"result": orders, "cached_at": time.time()}
    return orders