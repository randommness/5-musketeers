from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import product_pair_service

router = APIRouter(prefix="/product_pair", tags=["Product pairing"])

# GET /product_pair/all

@router.get("/all")
def get_product_pair(db: Session = Depends(get_db)):
    return product_pair_service.pair_product_recommendation(db)