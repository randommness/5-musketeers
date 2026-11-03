from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import api_catalog_service

router = APIRouter(prefix="/api", tags=["API: Catalog list"])

# For: Values for navigation and filter dropdowns

# GET /api/categories
@router.get("/categories")
def get_all_categories(db: Session = Depends(get_db)):
    return api_catalog_service.get_all_categories(db)

# GET /api/brands
@router.get("/brands")
def get_all_brands(db: Session = Depends(get_db)):
    return api_catalog_service.get_all_brands(db)

# GET /api/pet_types
@router.get("/pet_types")
def get_all_pet_types(db: Session = Depends(get_db)):
    return api_catalog_service.get_all_pet_types(db)
