from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import api_customer_dashboard_service

router = APIRouter(prefix="/api", tags=["API: Customer & Orders information"])

# For: Retrieve customer info or orders given customer_id

# GET /api/customers
@router.get("/customers")
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    return api_customer_dashboard_service.get_customer_profile(customer_id=customer_id, db=db)

# GET /api/orders
@router.get("/orders")
def get_all_brands(customer_id: str, db: Session = Depends(get_db)):
    return api_customer_dashboard_service.get_customer_orders(customer_id=customer_id, db=db)
