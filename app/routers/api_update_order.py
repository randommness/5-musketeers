from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import api_update_order_service

router = APIRouter(prefix="/api/orders", tags=["API: Update Order Status"])

# For: Updating orders for cancel or refund

# PATCH /api/orders/{order_id}/cancel
@router.patch("/{order_id}/cancel")
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    return api_update_order_service.cancel_order(order_id=order_id, db=db)

# PATCH /api/orders/{order_id}/refund
@router.patch("/{order_id}/refund")
def refund_request_order(order_id: str, db: Session = Depends(get_db)):
    return api_update_order_service.refund_request_order(order_id=order_id, db=db)