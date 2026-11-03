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


def goal_product_recommendation(db: Session):
    # For all users, based on their pet type AND brand preferences OR category preferences, recommend max 3 products for them.
    # We prioritize matches on brand and category preferences, then either. There can be more than 1 pair of brand-category preference.
    # WARNING: This query only returns first 5 customers (I'm controlling unnecessary LLM calls for now, remove later).
    result: Any = db.execute(
        text("""
        WITH goals AS (
            SELECT
                customer_id,
                pet_type,
                regexp_split_to_array(
                    trim(both '[]' FROM replace(product_preferences, '''', '')),
                    '\s*,\s*'
                ) AS product_preferences,
                regexp_split_to_array(
                    trim(both '[]' FROM replace(preferred_brands, '''', '')),
                    '\s*,\s*'
                ) AS preferred_brands
            FROM public.customer_info
        )
        SELECT
            g.customer_id,
            r.product_id,
            r.brand,
            r.pet_type,
            r.product_name,
            r.product_category,
            r.product_description,
            CONCAT(r.unit_price, ' ', r.currency) AS price,
            r.product_size,
            r.number_of_reviews,
            r.match_reason
        FROM goals g
        JOIN LATERAL (
            SELECT
                p.*,
                CASE
                    WHEN p.brand = ANY(g.preferred_brands)
                    AND p.product_category = ANY(g.product_preferences)
                        THEN 'brand_and_category_match'
                    WHEN p.brand = ANY(g.preferred_brands)
                        THEN 'brand_match'
                    ELSE 'category_match'
                END AS match_reason
            FROM public.product_info p
            WHERE p.pet_type = g.pet_type
            AND (
                    p.brand = ANY(g.preferred_brands)
                OR p.product_category = ANY(g.product_preferences)
            )
            ORDER BY
                CASE
                    WHEN p.brand = ANY(g.preferred_brands)
                    AND p.product_category = ANY(g.product_preferences) THEN 1
                    WHEN p.brand = ANY(g.preferred_brands) THEN 2
                    ELSE 3
                END,
                p.number_of_reviews DESC NULLS LAST,
                p.product_id
            LIMIT 2
        ) r ON TRUE
        ORDER BY
            g.customer_id,
            CASE r.match_reason
                WHEN 'brand_and_category_match' THEN 1
                WHEN 'brand_match' THEN 2
                ELSE 3
            END,
            r.number_of_reviews DESC NULLS LAST;
        """)
    ).fetchall()

    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d product recommendations", len(rows))
    
    system_prompt = """You are a product recommendation agent for a pet care business. Given two products, 
                    a match reason, and the user's pet_type, write one plain-text paragraph of 2-3 sentences 
                    recommending the products. For each product, include its name, a brief summary, and why it 
                    suits the user's pet based only on the provided brand and/or category preference match. Use 
                    only provided information. Do not invent goals, details, or follow-up questions. Do not use 
                    markdown."""

    # Group rows by customer_id — each customer can have up to 2 product rows
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        customer_id = row["customer_id"]
        grouped.setdefault(customer_id, []).append(row)
    logger.debug("Grouped into %d customers", len(grouped))


    # Separate cache hits from misses
    cached_results: dict[str, dict] = {}
    groups_to_process: list[tuple[str, list[dict]]] = []

    for customer_id, product_rows in grouped.items():
        cached = _cache.get(customer_id)
        if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for customer %s", customer_id)
            cached_results[customer_id] = cached["result"]
        else:
            logger.debug("Cache miss for customer %s — queued for LLM with %d product(s)", customer_id, len(product_rows))
            groups_to_process.append((customer_id, product_rows))

    # Fire all cache-miss LLM calls in parallel
    def call_llm(customer_id: str, product_rows: list[dict]) -> dict:
        ai_suggestion = chat(
            user_prompt=f"Customer ID: {customer_id}. Recommended products: {json.dumps(product_rows)}",
            system_prompt=system_prompt
        )
        entry = {
            "customer_id": customer_id,
            "recommended_products": product_rows,
            "ai_suggestion": ai_suggestion
        }
        _cache[customer_id] = {"result": entry, "cached_at": time.time()}
        logger.debug("LLM call complete and cached for customer %s", customer_id)
        return entry

    llm_results: dict[str, dict] = {}
    if groups_to_process:
        logger.debug("Firing %d LLM calls in parallel", len(groups_to_process))
        with ThreadPoolExecutor(max_workers=len(groups_to_process)) as executor:
            futures = {executor.submit(call_llm, cid, prows): cid for cid, prows in groups_to_process}
            for future in as_completed(futures):
                entry = future.result()
                llm_results[entry["customer_id"]] = entry

    # Reassemble output in original grouped order
    output = []
    for customer_id in grouped:
        if customer_id in cached_results:
            output.append(cached_results[customer_id])
        elif customer_id in llm_results:
            output.append(llm_results[customer_id])

    # Return list of all customers. Shape:
    # [{"customer_id": "CUST001", "recommended_products": [{...}, {...}], "ai_suggestion": "..."}, ...]
    return output