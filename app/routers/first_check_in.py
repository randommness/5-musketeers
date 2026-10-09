from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import check_in_service

router = APIRouter(prefix="/check_in", tags=["First Use Check In"])

# GET /portfolio/{user_id}
# GET /portfolio/{user_id}/summary

@router.get("/{user_id}")
def get_latest_order(user_id: int, db: Session = Depends(get_db)):
    return check_in_service.get_latest_order(db, user_id)