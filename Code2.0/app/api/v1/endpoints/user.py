from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.user_session import get_user_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_user_db)) -> UserResponse:
    service = UserService(db)
    try:
        user = service.register_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
def login(user_in: UserLogin, db: Session = Depends(get_user_db)) -> UserResponse:
    service = UserService(db)
    user = service.authenticate_user(user_in)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return UserResponse.model_validate(user)

