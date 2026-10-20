import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.llm import chat

logger = logging.getLogger(__name__)

# Caching
_cache: dict = {}
CACHE_TTL_SECONDS = 3600


def get_latest_order(db: Session):
    # For all users, get the latest delivered order, storing them as dictionaries.
    # WARNING: This query only returns first 5 customers (I'm controlling unnecessary LLM calls for now, remove later).
    result: Any = db.execute(
        text("""
        WITH latest_orders AS (
            SELECT
                o.customer_id,
                o.order_id,
                ROW_NUMBER() OVER (
                    PARTITION BY o.customer_id
                    ORDER BY o.order_date DESC, o.order_id DESC
                ) AS rn
            FROM orders o
        )
        SELECT
            o.customer_id,
            oi.product_id,
            p.product_name,
            p.product_category,
            p.pet_type,
            p.brand,
            p.product_description,
            CONCAT(p.product_weight, ' ', p.weight_unit) AS product_weight,
            p.packaging_type,
            p.product_size,
            p.product_rating,
            p.number_of_reviews
        FROM latest_orders lo
        INNER JOIN orders o
            ON o.order_id = lo.order_id
        INNER JOIN order_item oi
            ON o.order_id = oi.order_id
        INNER JOIN product_info p
            ON oi.product_id = p.product_id
        WHERE lo.rn = 1
        ORDER BY lo.customer_id ASC
        """)
    ).fetchall()

    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d users", len(rows))

    system_prompt = """You are a helpful, check-in agent working for a pet care business that offers pet care products.
                Users may encounter difficulty using their product when they recieve it or place an order for it.
                Based on the data provided by the user, your objective is to analyse this data and generate a short summary of around 1 paragraph, summarising
                how to use the product, tips and tricks, what users have said in general, and anything you think can help the user. You must be concise, and go straight to the point.
                Don't return markdown, return plain text. Do not ask for follow up, do not just describe the product, but share insights and how can the pet use this product
                meaningfully & how the owner can help."""

    # Separate cache hits from misses — no need to call LLM for cached users
    cached_results: dict[str, dict] = {}
    rows_to_process: list[dict] = []

    for row in rows:
        customer_id = row["customer_id"]
        cached = _cache.get(customer_id)
        if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for user %s", customer_id)
            cached_results[customer_id] = cached["result"]
        else:
            logger.debug("Cache miss for user %s — queued for LLM", customer_id)
            rows_to_process.append(row)

    # Fire all cache-miss LLM calls in parallel
    def call_llm(row: dict) -> dict:
        customer_id = row["customer_id"]
        ai_suggestion = chat(
            user_prompt=f"User data: {json.dumps(row)}",
            system_prompt=system_prompt
        )
        entry = {**row, "ai_suggestion": ai_suggestion}
        _cache[customer_id] = {"result": entry, "cached_at": time.time()}
        logger.debug("LLM call complete and cached for user %s", customer_id)
        return entry

    llm_results: dict[str, dict] = {}
    if rows_to_process:
        logger.debug("Firing %d LLM calls in parallel", len(rows_to_process))
        with ThreadPoolExecutor(max_workers=len(rows_to_process)) as executor:
            futures = {executor.submit(call_llm, row): row["customer_id"] for row in rows_to_process}
            for future in as_completed(futures):
                entry = future.result()
                llm_results[entry["customer_id"]] = entry

    # Reassemble output in original row order
    output = []
    for row in rows:
        customer_id = row["customer_id"]
        if customer_id in cached_results:
            output.append(cached_results[customer_id])
        elif customer_id in llm_results:
            output.append(llm_results[customer_id])

    # Return list of all users. Shape:
    # [{"customer_id": "CUST001", "product_name": ..., "ai_suggestion": ...}, ...]
    return output