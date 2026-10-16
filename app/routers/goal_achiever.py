from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import goal_achiever_service

router = APIRouter(prefix="/achieve_goals", tags=["Help user achieve pet goals"])

# GET /goal_achiever/{user_id}

@router.get("/all")
def get_latest_order(db: Session = Depends(get_db)):
    return goal_achiever_service.goal_product_recommendation(db)