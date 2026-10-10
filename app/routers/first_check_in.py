from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import check_in_service

router = APIRouter(prefix="/check_in", tags=["First Use Check In"])

# GET /first_check_in/{user_id}

@router.get("/all")
def get_latest_order(db: Session = Depends(get_db)):
    return check_in_service.get_latest_order(db)