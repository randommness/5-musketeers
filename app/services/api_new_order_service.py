import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def create_order(
    customer_id: str,
    shop_id: str,
    order_channel: str,
    total_order_value: Decimal,
    discount_applied: Decimal,
    delivery_fee_charged: Decimal,
    payment_method: str,
    delivery_method: str,
    estimated_delivery_date: date,
    items: list[dict[str, Any]],
    db: Session,
):
    try:
        # Insert into the orders table first.
        order_id: Any = db.execute(
            text("""
            SELECT 
                'ORD' || LPAD((SUBSTRING(order_id FROM '[0-9]+')::INTEGER + 1)::TEXT, 3, '0') AS next_value
            FROM public.orders
            ORDER BY order_id DESC
            LIMIT 1;
            """)
        ).scalar_one()

        db.execute(
            text("""
            INSERT INTO public.orders (order_id, customer_id, shop_id, order_date, order_status, order_channel, total_order_value, 
                discount_applied, delivery_fee_charged, final_amount_paid, payment_method, payment_status, delivery_method, 
                estimated_delivery_date, actual_delivery_date, return_status, refund_amount)
            VALUES (:order_id, :customer_id, :shop_id, :order_date, :order_status, :order_channel, :total_order_value, 
                :discount_applied, :delivery_fee_charged, :final_amount_paid, :payment_method, :payment_status, :delivery_method, 
                :estimated_delivery_date, :actual_delivery_date, :return_status, :refund_amount)
            """),
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "shop_id": shop_id,
                "order_date": datetime.now().replace(microsecond=0),
                "order_status": "New",
                "order_channel": order_channel,
                "total_order_value": total_order_value,
                "discount_applied": discount_applied,
                "delivery_fee_charged": delivery_fee_charged,
                "final_amount_paid": total_order_value - discount_applied + delivery_fee_charged,
                "payment_method": payment_method,
                "payment_status": "Pending",
                "delivery_method": delivery_method,
                "estimated_delivery_date": estimated_delivery_date,
                "actual_delivery_date": None,
                "return_status": None,
                "refund_amount": None,
            }
        )

        # Now insert into the order_item table — one row per item.
        next_item_seq: Any = db.execute(
            text("""
            SELECT (SUBSTRING(order_item_id FROM '[0-9]+')::INTEGER + 1) AS next_seq
            FROM public.order_item
            ORDER BY order_item_id DESC
            LIMIT 1;
            """)
        ).scalar_one()

        for i, item in enumerate(items):
            order_item_id = f"OI0{str(next_item_seq + i).zfill(3)}"
            db.execute(
                text("""
                INSERT INTO public.order_item (order_item_id, order_id, product_id, quantity_purchased, unit_price, item_discount, subtotal)
                VALUES (:order_item_id, :order_id, :product_id, :quantity_purchased, :unit_price, :item_discount, :subtotal)
                """),
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": item["product_id"],
                    "quantity_purchased": item["quantity_purchased"],
                    "unit_price": item["unit_price"],
                    "item_discount": item["item_discount"],
                    "subtotal": (item["unit_price"] - item["item_discount"]) * item["quantity_purchased"],
                }
            )

        db.commit()
        logger.debug("Order %s created for customer %s with %d item(s)", order_id, customer_id, len(items))

        return {
            "order_id": order_id,
            "order_status": "New",
            "payment_status": "Pending",
            "item_count": len(items),
            "success": True,
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Failed to create order for customer %s: %s", customer_id, e, exc_info=True)
        return {"success": False}
