import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.engine import CursorResult

logger = logging.getLogger(__name__)


def cancel_order(order_id: str, db: Session):
    logger.debug("Attempting to cancel order_id %s", order_id)

    try:
        result: CursorResult = db.execute(
            text("""
            UPDATE public.orders 
            SET order_status = 'Cancelled' 
            WHERE UPPER(order_id) = UPPER(:order_id)
            """),
            {"order_id": order_id}
        )

        if result.rowcount == 0:
            logger.warning("Cancel failed — no order found with order_id %s", order_id)
            return {"success": False, "message": f"Order {order_id} not found"}

        db.commit()
        logger.debug("Order %s successfully cancelled", order_id)
        return {"success": True, "message": f"Order {order_id} has been cancelled"}

    except Exception as e:
        db.rollback()
        logger.error("Error cancelling order_id %s: %s", order_id, e, exc_info=True)
        return {"success": False, "message": "An error occurred while cancelling the order"}


def refund_request_order(order_id: str, db: Session):
    logger.debug("Attempting to request refund for order_id %s", order_id)

    try:
        result: CursorResult = db.execute(
            text("""
            UPDATE public.orders 
            SET return_status = 'Requested', refund_amount = 0 
            WHERE UPPER(order_id) = UPPER(:order_id)
            """),
            {"order_id": order_id}
        )

        if result.rowcount == 0:
            logger.warning("Refund request failed — no order found with order_id %s", order_id)
            return {"success": False, "message": f"Order {order_id} not found"}

        db.commit()
        logger.debug("Refund successfully requested for order %s", order_id)
        return {"success": True, "message": f"Refund requested for order {order_id}"}

    except Exception as e:
        db.rollback()
        logger.error("Error requesting refund for order_id %s: %s", order_id, e, exc_info=True)
        return {"success": False, "message": "An error occurred while requesting the refund"}
