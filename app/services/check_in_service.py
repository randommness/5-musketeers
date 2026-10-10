import json
import logging
import time
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.llm import chat

logger = logging.getLogger(__name__)

# Caching
_cache: dict = {}
CACHE_TTL_SECONDS = 1800


def get_latest_order(db: Session):
    # For all users, get the latest delivered order, storing them as dictionaries.
    result: Any = db.execute(
        text("""
        WITH latest_purchase AS (
            SELECT
                ps.user_id,
                ps.product_id,
                ps.order_time,
                ROW_NUMBER() OVER (
                    PARTITION BY ps.user_id
                    ORDER BY ps.order_time DESC
                ) AS rn
            FROM public.purchases ps
            WHERE ps.delivery_status = 'Delivered'
        )
        SELECT
            lp.user_id,
            pdt.product_name,
            pdt.category_name,
            pdt.short_desc,
            pdt.price,
            pdt.stars
        FROM latest_purchase lp
        INNER JOIN public.products pdt
            ON lp.product_id = pdt.product_id
        WHERE lp.rn = 1
        ORDER BY lp.user_id;
        """)
    ).fetchall()

    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d users", len(rows))

    # For each user, check if we can use cache. If either cache expired, or user order is new, then call LLM for AI suggestion.
    output = []
    system_prompt = """You are a helpful, check-in agent working for a pet care business that offers pet care products, treatments, and services.
                Users may encounter difficulty using their product or understanding their pet treatment / service when they recieve it or place an order for it.
                Based on the data provided by the user, your objective is to analyse this data and generate a short summary of around 1 paragraph, summarising
                how to use the product, tips and tricks, and anything you think can help the user. You must be concise, and go straight to the point. Don't return markdown,
                return plain text. Do not ask for follow up, do not just describe the product, but share insights and how can the pet use this product / how will the treatment
                or service help the pet meaningfully."""
    
    for row in rows:
        user_id = row["user_id"]

        cached = _cache.get(user_id)
        if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
            logger.debug("Cache hit for user %s", user_id)
            output.append(cached["result"])
            continue

        logger.debug("Cache miss for user %s — calling LLM", user_id)
        ai_suggestion = chat(
            user_prompt=f"User data: {json.dumps(row)}",
            system_prompt=system_prompt
        )

        # Now build the final entry (JSON payload) and append it to the output and cache
        entry = {**row, "ai_suggestion": ai_suggestion}
        _cache[user_id] = {"result": entry, "cached_at": time.time()}
        output.append(entry)

    # Return list of all users. The structure would be like:
    # [{"user_id": 1, "product_name": ..., "ai_suggestion": ...}, {...}, ...]
    return output