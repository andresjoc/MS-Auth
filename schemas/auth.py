from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    id_city: int
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    birth_date: date


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id_user: int
    id_city: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    id_user: int
    id_city: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    email: EmailStr
    exp: int
    type: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: int
    email: EmailStr


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenUser(BaseModel):
    user_id: int
    email: EmailStr
