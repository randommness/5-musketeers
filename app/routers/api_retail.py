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
def get_product_list(
    db: Session = Depends(get_db),
    product_id: Optional[str] = None,
    product_category: Optional[str] = None,
    pet_type: Optional[str] = None,
    brand: Optional[str] = None,
    unit_price: Optional[str] = None,
    currency: Optional[str] = None,
    product_weight: Optional[str] = None,
    weight_unit: Optional[str] = None,
    packaging_type: Optional[str] = None,
    product_size: Optional[str] = None,
    product_rating: Optional[str] = None,
    number_of_reviews: Optional[str] = None,
    subscription_availability: Optional[bool] = None,
    limit: Optional[int] = None,
):
    return api_retail_services.list_products(
        db=db,
        product_id=product_id,
        product_category=product_category,
        pet_type=pet_type,
        brand=brand,
        unit_price=unit_price,
        currency=currency,
        product_weight=product_weight,
        weight_unit=weight_unit,
        packaging_type=packaging_type,
        product_size=product_size,
        product_rating=product_rating,
        number_of_reviews=number_of_reviews,
        subscription_availability=subscription_availability,
        limit=limit,
    )