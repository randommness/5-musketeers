from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import api_login_service

router = APIRouter(prefix="/api/auth/login", tags=["API: User login"])

class LoginRequest(BaseModel):
    customer_id: str
    password: str

# POST /api/login
@router.post("")
def post_login_authentication(body: LoginRequest, db: Session = Depends(get_db)):
    return api_login_service.login(customer_id=body.customer_id, password=body.password, db=db)