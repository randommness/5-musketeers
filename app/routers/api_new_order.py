from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import api_new_order_service


router = APIRouter(prefix="/api/orders", tags=["API: New Order"])

# For: Creating a new order - insert into orders and order_item tables

class OrderItemRequest(BaseModel):
    product_id: str = Field(min_length=1)
    quantity_purchased: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    item_discount: Decimal = Field(ge=0)

class OrderRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    shop_id: str = Field(min_length=1)
    order_channel: str = Field(min_length=1)

    total_order_value: Decimal = Field(ge=0)
    discount_applied: Decimal = Field(ge=0)
    delivery_fee_charged: Decimal = Field(ge=0)

    payment_method: str = Field(min_length=1)
    delivery_method: str = Field(min_length=1)
    estimated_delivery_date: date

    items: list[OrderItemRequest] = Field(min_length=1)

# POST /api/orders
@router.post("")
def post_order(body: OrderRequest,db: Session = Depends(get_db)):
    return api_new_order_service.create_order(
        customer_id=body.customer_id,
        shop_id=body.shop_id,
        order_channel=body.order_channel,
        total_order_value=body.total_order_value,
        discount_applied=body.discount_applied,
        delivery_fee_charged=body.delivery_fee_charged,
        payment_method=body.payment_method,
        delivery_method=body.delivery_method,
        estimated_delivery_date=body.estimated_delivery_date,
        items=[item.model_dump() for item in body.items],
        db=db,
    )