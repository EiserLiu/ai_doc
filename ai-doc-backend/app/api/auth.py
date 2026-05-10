from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from app.services.auth_service import register_user, authenticate_user, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserInfo)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, req.username, req.password, req.company_name, req.phone)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
def get_me(current_user=Depends(get_current_user)):
    return current_user
