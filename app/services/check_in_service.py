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
CACHE_TTL_SECONDS = 3600


def get_latest_order(db: Session, user_id: int):
    # Cache check
    cached = _cache.get(user_id)
    if cached and (time.time() - cached["cached_at"]) < CACHE_TTL_SECONDS:
        logger.debug("Cache hit for user %s", user_id)
        return cached["result"]

    logger.debug("Cache miss for user %s — calling DB and LLM", user_id)

    # No cache found or that the cache expired, so call the actual API
    result: Any = db.execute(
        text("""
        SELECT pdt.product_name, pdt.category_name, pdt.short_desc, pdt.price, pdt.stars
        FROM public.purchases ps
        INNER JOIN public.products pdt
        ON ps.product_id = pdt.product_id
        WHERE ps.order_time IN 
        (SELECT MAX(order_time) 
        FROM public.purchases 
        WHERE user_id = :user_id
        AND delivery_status = 'Delivered')
        """),
        {"user_id": user_id}
    ).fetchall()

    results = [dict(row._mapping) for row in result]

    logger.debug("Latest order results for user %s: %s", user_id, results)

    system_prompt = """You are a helpful, check-in agent working for a pet care business that offers pet care products, treatments, and services. 
                    Users may encounter difficulty using their product or understanding their pet treatment / service when they recieve it or place an order for it. 
                    Based on the data provided by the user, your objective is to analyse this data and generate a short summary of around 1 paragraph, summarising 
                    how to use the product, tips and tricks, and anything you think can help the user. You must be concise, and go straight to the point. Don't return markdown, 
                    return plain text. Do not ask for follow up, do not just describe the product, but share insights and how can the user use this product / how will the treatment 
                    or service help the pet meaningfully."""

    ai_suggestion = chat(user_prompt=f"User data: {json.dumps(results)}",
                         system_prompt=system_prompt)

    final = {**results[0], "ai_suggestion": ai_suggestion} if results else {}

    # --- Store in cache ---
    _cache[user_id] = {"result": final, "cached_at": time.time()}
    logger.debug("Cached result for user %s", user_id)

    return final