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

def _parse_range_filter(column: str, value: str, params: dict) -> str:
    """Parse >n / <n / n into a SQL condition. Bound value is stored in params."""
    param_key = column
    if value.startswith(">="):
        params[param_key] = float(value[2:])
        return f"{column} >= :{param_key}"
    elif value.startswith(">"):
        params[param_key] = float(value[1:])
        return f"{column} >= :{param_key}"
    elif value.startswith("<="):
        params[param_key] = float(value[2:])
        return f"{column} <= :{param_key}"
    elif value.startswith("<"):
        params[param_key] = float(value[1:])
        return f"{column} <= :{param_key}"
    else:
        params[param_key] = float(value)
        return f"{column} = :{param_key}"


def list_products(
    db: Session,
    product_id: Optional[str] = None,
    product_category: Optional[str] = None,
    pet_type: Optional[str] = None,
    brand: Optional[str] = None,
    unit_price: Optional[str] = None,
    currency: Optional[str] = None,
    product_weight: Optional[str] = None,
    weight_unit: Optional[str] = None,
    packaging_type: Optional[str] = None,
    product_size: Optional[str] = None,
    product_rating: Optional[str] = None,
    number_of_reviews: Optional[str] = None,
    subscription_availability: Optional[bool] = None,
    limit: Optional[int] = None,
):
    # Only cache the fully unfiltered result — filtered/limited queries are too varied to cache reliably
    is_unfiltered = not any([
        product_id, product_category, pet_type, brand, unit_price, currency,
        product_weight, weight_unit, packaging_type, product_size,
        product_rating, number_of_reviews, subscription_availability is not None,
        limit is not None,
    ])

    if is_unfiltered:
        cached = _cache.get("all_products")
        if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for 'all_products' — returning %d cached product(s)", len(cached["result"]))
            return cached["result"]
        logger.debug("Cache miss for 'all_products' — querying DB")

    base_query = """
        SELECT product_id,
               product_name,
               product_category,
               pet_type,
               brand,
               product_description,
               unit_price,
               currency,
               product_weight,
               weight_unit,
               packaging_type,
               product_size,
               product_rating,
               number_of_reviews,
               product_expiry_date,
               subscription_availability
        FROM public.product_info
    """

    conditions: list[str] = []
    params: dict = {}

    # Exact-match filters
    if product_id:
        conditions.append("product_id = :product_id")
        params["product_id"] = product_id
    if product_category:
        conditions.append("product_category = :product_category")
        params["product_category"] = product_category
    if pet_type:
        conditions.append("pet_type = :pet_type")
        params["pet_type"] = pet_type
    if brand:
        conditions.append("brand = :brand")
        params["brand"] = brand
    if currency:
        conditions.append("currency = :currency")
        params["currency"] = currency
    if weight_unit:
        conditions.append("weight_unit = :weight_unit")
        params["weight_unit"] = weight_unit
    if packaging_type:
        conditions.append("packaging_type = :packaging_type")
        params["packaging_type"] = packaging_type
    if product_size:
        conditions.append("product_size = :product_size")
        params["product_size"] = product_size
    if subscription_availability is not None:
        conditions.append("subscription_availability = :subscription_availability")
        params["subscription_availability"] = subscription_availability

    # Range filters: >n / >=n / <n / <=n / n (exact)
    if unit_price:
        conditions.append(_parse_range_filter("unit_price", unit_price, params))
    if product_weight:
        conditions.append(_parse_range_filter("product_weight", product_weight, params))
    if product_rating:
        conditions.append(_parse_range_filter("product_rating", product_rating, params))
    if number_of_reviews:
        conditions.append(_parse_range_filter("number_of_reviews", number_of_reviews, params))

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    limit_clause = f" LIMIT {limit}" if limit is not None else ""
    result: Any = db.execute(
        text(base_query + where_clause + " ORDER BY product_id ASC" + limit_clause + ";"),
        params
    ).fetchall()

    rows = [dict(row._mapping) for row in result]

    if not rows and conditions:
        logger.warning("No products found for applied filters")
    else:
        logger.debug("SQL returned %d product(s)", len(rows))

    if is_unfiltered:
        _cache["all_products"] = {"result": rows, "cached_at": time.time()}

    return rows