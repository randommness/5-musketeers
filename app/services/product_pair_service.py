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


def pair_product_recommendation(db: Session):
    # For all users, based on their pet type AND brand preferences OR category preferences, recommend max 3 products for them.
    # We prioritize matches on brand and category preferences, then either. There can be more than 1 pair of brand-category preference.
    # WARNING: This query only returns first 5 customers (I'm controlling unnecessary LLM calls for now, remove later).
    order_pattern: Any = db.execute(
        text(""" 
        WITH order_products AS (
            SELECT DISTINCT
                order_id,
                product_id
            FROM order_item
        ),
        pair_counts AS (
            SELECT
                a.product_id AS product_a_id,
                b.product_id AS product_b_id,
                COUNT(*) AS bought_together_count
            FROM order_products AS a
            JOIN order_products AS b
                ON a.order_id = b.order_id
            AND a.product_id <> b.product_id
            JOIN product_info AS pa
                ON pa.product_id = a.product_id
            JOIN product_info AS pb
                ON pb.product_id = b.product_id
            WHERE
                NULLIF(TRIM(pa.pet_type), '') IS NOT NULL
                AND LOWER(TRIM(pa.pet_type)) = LOWER(TRIM(pb.pet_type))
            GROUP BY
                a.product_id,
                b.product_id
        ),
        ranked_pairs AS (
            SELECT
                product_a_id,
                product_b_id,
                bought_together_count,
                ROW_NUMBER() OVER (
                    PARTITION BY product_a_id
                    ORDER BY bought_together_count DESC, product_b_id
                ) AS recommendation_rank
            FROM pair_counts
        )
        SELECT
            -- Product A
            r.product_a_id,
            pa.brand AS product_a_brand,
            pa.product_name AS product_a_name,
            pa.product_category AS product_a_category,
            pa.product_description AS product_a_description,
            CONCAT(pa.unit_price, ' ', pa.currency) AS product_a_price,
            CONCAT(pa.product_weight, ' ', pa.weight_unit) AS product_a_size,

            -- Product B
            r.product_b_id,
            pb.brand AS product_b_brand,
            pb.product_name AS product_b_name,
            pb.product_category AS product_b_category,
            pb.product_description AS product_b_description,
            CONCAT(pb.unit_price, ' ', pb.currency) AS product_b_price,
            CONCAT(pb.product_weight, ' ', pb.weight_unit) AS product_b_size,

            -- Co-purchase statistics
            r.bought_together_count,
            r.recommendation_rank
        FROM ranked_pairs AS r
        JOIN product_info AS pa
            ON pa.product_id = r.product_a_id
        JOIN product_info AS pb
            ON pb.product_id = r.product_b_id
        WHERE r.recommendation_rank <= 3
            AND r.product_a_id IN ('PRD003', 'PRD004', 'PRD023', 'PRD041', 'PRD078')
        ORDER BY
            r.product_a_id,
            r.recommendation_rank;
        """)
    ).fetchall()

    order_rows = [dict(row._mapping) for row in order_pattern]
    logger.debug("SQL returned %d product pairings in order records", len(order_rows))

    product_pattern: Any = db.execute(
        text(""" 
        WITH ranked_recommendations AS (
            SELECT
                a.product_id AS product_a_id,
                b.product_id AS product_b_id,

                ROW_NUMBER() OVER (
                    PARTITION BY a.product_id
                    ORDER BY
                        -- Same-category products come first.
                        CASE
                            WHEN LOWER(TRIM(b.product_category)) =
                                LOWER(TRIM(a.product_category))
                            THEN 0
                            ELSE 1
                        END,

                        -- Within the same category: most reviews first.
                        CASE
                            WHEN LOWER(TRIM(b.product_category)) =
                                LOWER(TRIM(a.product_category))
                            THEN b.number_of_reviews
                        END DESC NULLS LAST,

                        -- Same-category tie-breaker, and main fallback criterion.
                        ABS(b.unit_price - a.unit_price),

                        -- Fallback tie-breaker: most reviews first.
                        b.number_of_reviews DESC NULLS LAST,

                        -- Final tie-breaker for consistent results.
                        b.product_id
                ) AS recommendation_rank

            FROM product_info AS a
            JOIN product_info AS b
                ON b.product_id <> a.product_id

                -- Always require the same brand.
                AND LOWER(TRIM(b.brand)) = LOWER(TRIM(a.brand))

                -- Always require the same pet type.
                AND LOWER(TRIM(b.pet_type)) = LOWER(TRIM(a.pet_type))

                -- Compare prices in the same currency.
                AND LOWER(TRIM(b.currency)) = LOWER(TRIM(a.currency))

            WHERE NULLIF(TRIM(a.brand), '') IS NOT NULL
            AND NULLIF(TRIM(a.pet_type), '') IS NOT NULL
            AND NULLIF(TRIM(a.currency), '') IS NOT NULL
            AND a.unit_price IS NOT NULL
            AND b.unit_price IS NOT NULL
        )
        SELECT
            -- Product A
            r.product_a_id,
            pa.brand AS product_a_brand,
            pa.product_name AS product_a_name,
            pa.product_category AS product_a_category,
            pa.product_description AS product_a_description,
            CONCAT(pa.unit_price, ' ', pa.currency) AS product_a_price,
            CONCAT(pa.product_weight, ' ', pa.weight_unit) AS product_a_size,

            -- Recommended product B
            r.product_b_id,
            pb.brand AS product_b_brand,
            pb.product_name AS product_b_name,
            pb.product_category AS product_b_category,
            pb.product_description AS product_b_description,
            CONCAT(pb.unit_price, ' ', pb.currency) AS product_b_price,
            CONCAT(pb.product_weight, ' ', pb.weight_unit) AS product_b_size,

            r.recommendation_rank

        FROM ranked_recommendations AS r
        JOIN product_info AS pa
            ON pa.product_id = r.product_a_id
        JOIN product_info AS pb
            ON pb.product_id = r.product_b_id

        WHERE r.recommendation_rank <= 2
            AND r.product_a_id IN ('PRD001', 'PRD002', 'PRD003', 'PRD004', 'PRD005')

        ORDER BY
            r.product_a_id,
            r.recommendation_rank;
        """)
    ).fetchall()

    product_rows = [dict(row._mapping) for row in product_pattern]
    logger.debug("SQL returned %d product pairings in product list", len(product_rows))

    system_prompt = """You are a smart product pairing agent for a pet care business. You are given data about a product (Product A) and two signals:
                    1. Order pattern signal: products that other customers commonly bought together with Product A (association rules from real order history).
                    2. Product similarity signal: products from the same brand and pet type with similar price points or category.
                    Your task is to recommend exactly 2 products to pair with Product A. Use both signals to reason about which pairings are most meaningful.
                    Prioritise products that appear in both signals. If a product only appears in one signal, use your judgement.
                    You MUST respond with valid JSON only, with no extra text before or after. Use this exact format:
                    {"recommendations": [{"product_b_id": "<id>", "reason": "<one sentence>"}, {"product_b_id": "<id>", "reason": "<one sentence>"}]}
                    Only use product_b_id values that appear in the provided signals. Do not invent IDs."""

    # Group both signals by product_a_id
    # order_signal:   { product_a_id: [rows of co-purchased pairs] }
    # product_signal: { product_a_id: [rows of similarity-based pairs] }
    order_signal: dict[str, list[dict]] = {}
    for row in order_rows:
        pid = row["product_a_id"]
        order_signal.setdefault(pid, []).append(row)

    product_signal: dict[str, list[dict]] = {}
    for row in product_rows:
        pid = row["product_a_id"]
        product_signal.setdefault(pid, []).append(row)

    # Union of all product_a_ids across both signals
    all_product_a_ids = sorted(set(order_signal.keys()) | set(product_signal.keys()))
    logger.debug("Grouped into %d unique Product A entries", len(all_product_a_ids))

    # Separate cache hits from misses
    cached_results: dict[str, dict] = {}
    to_process: list[str] = []

    for product_a_id in all_product_a_ids:
        cached = _cache.get(product_a_id)
        if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for product_a_id %s", product_a_id)
            cached_results[product_a_id] = cached["result"]
        else:
            logger.debug("Cache miss for product_a_id %s — queued for LLM", product_a_id)
            to_process.append(product_a_id)

    # Fire all cache-miss LLM calls in parallel
    def call_llm(product_a_id: str) -> dict:
        o_rows = order_signal.get(product_a_id, [])
        p_rows = product_signal.get(product_a_id, [])

        # Derive product A info from whichever signal has it
        source = o_rows[0] if o_rows else p_rows[0]
        # product_a_id lives at the top level of entry — not duplicated inside product_a_info
        product_a_info = {
            "product_a_name":        source["product_a_name"],
            "product_a_brand":       source["product_a_brand"],
            "product_a_category":    source["product_a_category"],
            "product_a_description": source["product_a_description"],
            "product_a_price":       source["product_a_price"],
            "product_a_size":        source["product_a_size"],
        }

        # Build product_b lookup before calling LLM — keyed by product_b_id,
        # keeping only product_b_* fields (strips product_a_* and internal scoring fields)
        _internal_fields = {"bought_together_count", "recommendation_rank"}
        all_pairs: dict[str, dict] = {}
        for r in o_rows + p_rows:
            b_id = r["product_b_id"]
            if b_id not in all_pairs:  # first occurrence wins (highest rank from SQL ordering)
                all_pairs[b_id] = {
                    k: v for k, v in r.items()
                    if not k.startswith("product_a_") and k not in _internal_fields
                }

        user_prompt = (
            f"Product A: {json.dumps(product_a_info)}. "
            f"Order pattern signal (co-purchased by other customers): {json.dumps(o_rows)}. "
            f"Product similarity signal (same brand, pet type, similar price): {json.dumps(p_rows)}."
        )
        print(user_prompt)

        raw_response = chat(user_prompt=user_prompt, system_prompt=system_prompt)

        # Parse LLM JSON — validate every recommended product_b_id against actual pair data
        # Any hallucinated or duplicate ID is silently dropped
        recommended_pairs = []
        seen_ids: set[str] = set()
        try:
            llm_json = json.loads(raw_response)
            recommendations = llm_json.get("recommendations", [])

            for rec in recommendations[:2]:  # enforce max 2
                b_id = rec.get("product_b_id")
                if b_id and b_id in all_pairs and b_id not in seen_ids:
                    pair = {**all_pairs[b_id], "reason": rec.get("reason", "")}
                    recommended_pairs.append(pair)
                    seen_ids.add(b_id)
                else:
                    logger.warning("LLM recommended invalid/duplicate product_b_id '%s' for product_a_id %s — skipped", b_id, product_a_id)

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning("Failed to parse LLM JSON for product_a_id %s: %s — raw: %s", product_a_id, e, raw_response)

        logger.debug("Resolved %d recommended pair(s) for product_a_id %s", len(recommended_pairs), product_a_id)

        entry = {
            "product_a_id":      product_a_id,
            "product_a_info":    product_a_info,
            "recommended_pairs": recommended_pairs,
        }
        _cache[product_a_id] = {"result": entry, "cached_at": time.time()}
        logger.debug("LLM call complete and cached for product_a_id %s", product_a_id)
        return entry

    llm_results: dict[str, dict] = {}
    if to_process:
        logger.debug("Firing %d LLM calls in parallel", len(to_process))
        with ThreadPoolExecutor(max_workers=len(to_process)) as executor:
            futures = {executor.submit(call_llm, pid): pid for pid in to_process}
            for future in as_completed(futures):
                entry = future.result()
                llm_results[entry["product_a_id"]] = entry

    # Reassemble output in sorted product_a_id order
    output = []
    for product_a_id in all_product_a_ids:
        if product_a_id in cached_results:
            output.append(cached_results[product_a_id])
        elif product_a_id in llm_results:
            output.append(llm_results[product_a_id])

    # Return list of all product A entries. Shape:
    # [{"product_a_id": "P001", "product_a_info": {...},
    #   "recommended_pairs": [{"product_b_id": "P045", "product_b_name": ..., "reason": "..."}, ...]}, ...]
    return output