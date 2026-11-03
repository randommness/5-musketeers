import logging
from typing import Any, Optional
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def create_review(
    customer_id: str,
    order_id: str,
    product_id: str,
    product_rating: int,
    feedback_comment: str,
    complaint_category: Optional[str],
    complaint_status: Optional[str],
    preferred_promotion_type: str,
    db: Session,
):
    try:
        # Generate the next feedback_id
        feedback_id: Any = db.execute(
            text("""
            SELECT 'FB' || LPAD((SUBSTRING(feedback_id FROM '[0-9]+')::INTEGER + 1)::TEXT, 3, '0') AS next_value
            FROM public.customer_feedback
            ORDER BY feedback_id DESC
            LIMIT 1;
            """)
        ).scalar_one()

        db.execute(
            text("""
            INSERT INTO public.customer_feedback (
                feedback_id, customer_id, order_id, product_id,
                product_rating, feedback_comment, feedback_date, complaint_category,
                complaint_status, customer_satisfaction_score, preferred_promotion_type
            )
            VALUES (
                :feedback_id, :customer_id, :order_id, :product_id,
                :product_rating, :feedback_comment, :feedback_date, :complaint_category,
                :complaint_status, :customer_satisfaction_score, :preferred_promotion_type
            )
            """),
            {
                "feedback_id": feedback_id,
                "customer_id": customer_id,
                "order_id": order_id,
                "product_id": product_id,
                "product_rating": product_rating,
                "feedback_comment": feedback_comment,
                "feedback_date": datetime.now().replace(microsecond=0),
                "complaint_category": complaint_category,
                "complaint_status": complaint_status,
                "customer_satisfaction_score": product_rating,
                "preferred_promotion_type": preferred_promotion_type,
            }
        )

        db.commit()
        logger.debug("Review %s created for customer %s on product %s", feedback_id, customer_id, product_id)

        return {
            "feedback_id": feedback_id,
            "customer_id": customer_id,
            "product_rating": product_rating,
            "success": True,
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to create review for customer %s on product %s: %s", customer_id, product_id, e, exc_info=True)
        return {"success": False}
