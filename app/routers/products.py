from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import products_service

router = APIRouter(prefix="/products", tags=["Product List"])

# GET /products/all

@router.get("/all")
def get_products_list(db: Session = Depends(get_db)):
    return products_service.get_products_list(db)