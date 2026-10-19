from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import api_retail_services

router = APIRouter(prefix="/api", tags=["API: Promotions, Shops & Products"])

# For: Getting the list of promotions and shops

# GET /api/promotions
@router.get("/promotions")
def get_promotions_list(db: Session = Depends(get_db)):
    return api_retail_services.list_all_promotions(db)

@router.get("/shops")
def get_shops_list(db: Session = Depends(get_db)):
    return api_retail_services.list_all_shops(db)

# GET /api/products
@router.get("/products")
def get_product_list(db: Session = Depends(get_db), product_id: Optional[str] = None):
    return api_retail_services.list_products(db=db, product_id=product_id)