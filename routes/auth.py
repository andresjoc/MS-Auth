from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth_guard import get_current_user_from_token
from dependencies.current_user import get_current_active_user
from models.user import AppUser, AuthCredential, City
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    TokenResponse,
    TokenRefreshResponse,
    UserResponse,
    VerifyTokenResponse,
)
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from services.password_service import hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(AppUser).filter(AppUser.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    city = db.query(City).filter(City.id_city == payload.id_city).first()
    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found",
        )

    user = AppUser(
        id_city=payload.id_city,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        birth_date=payload.birth_date,
    )

    db.add(user)
    db.flush()

    credential = AuthCredential(
        id_user=user.id_user,
        password_hash=hash_password(payload.password),
        is_active=True,
    )

    db.add(credential)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.email == payload.email).first()
    credential = user.credential if user is not None else None

    if credential is None or not verify_password(payload.password, credential.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(user.id_user, user.email)
    refresh_token = create_refresh_token(user.id_user, user.email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_user = decode_refresh_token(payload.refresh_token)

    user = db.query(AppUser).filter(AppUser.id_user == token_user.user_id).first()

    if user is None or user.email != token_user.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.credential is None or not user.credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(user.id_user, user.email)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: AppUser = Depends(get_current_active_user)):
    return current_user


@router.get("/verify", response_model=VerifyTokenResponse)
def verify_token(token_user: dict = Depends(get_current_user_from_token)):
    return {
        "valid": True,
        "user_id": token_user["user_id"],
        "email": token_user["email"],
    }
