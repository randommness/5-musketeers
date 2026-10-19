import logging
import time
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

def login(customer_id: str, password: str, db: Session):
    count: Any = db.execute(
        text("""
        SELECT COUNT(*) 
        FROM public.credentials
        WHERE customer_id = :customer_id AND password = :password
        """),
        {"customer_id": customer_id, "password": password}
    ).scalar_one()

    authenticated = bool(count == 1)

    logger.debug(f"Login for user {customer_id} : {authenticated}")

    return {"authenticated": authenticated}