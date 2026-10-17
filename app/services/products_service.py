import logging
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

def get_products_list(db: Session):
    # Returns the full product catalogue from product_info.
    result: Any = db.execute(
        text("""
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
        FROM public.product_info;
        """)
    ).fetchall()

    rows = [dict(row._mapping) for row in result]
    logger.debug("SQL returned %d products", len(rows))

    return rows