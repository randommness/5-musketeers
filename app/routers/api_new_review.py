from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import api_new_review_service


router = APIRouter(prefix="/api/reviews", tags=["API: New Review"])

# For: Creating a new review - insert into customer_feedback table

class ReviewLoad(BaseModel):
    customer_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_rating: int = Field(ge=1, le=5)
    feedback_comment: str = Field(min_length=1)
    complaint_category: Optional[str] = None
    complaint_status: Optional[str] = None
    preferred_promotion_type: str = Field(min_length=1)

# POST /api/reviews
@router.post("")
def post_review(body: ReviewLoad, db: Session = Depends(get_db)):
    return api_new_review_service.create_review(
        customer_id=body.customer_id,
        order_id=body.order_id,
        product_id=body.product_id,
        product_rating=body.product_rating,
        feedback_comment=body.feedback_comment,
        complaint_category=body.complaint_category,
        complaint_status=body.complaint_status,
        preferred_promotion_type=body.preferred_promotion_type,
        db=db,
    )
