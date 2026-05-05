from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from config.environment import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from schemas.auth import TokenPayload, TokenUser


def create_access_token(user_id: int, email: str) -> tuple[str, int]:
    expires_in = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire_at,
        "type": "access",
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires_in


def create_refresh_token(user_id: int, email: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire_at,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise unauthorized from exc
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc

    subject = payload.get("sub")
    email = payload.get("email")
    token_type = payload.get("type")
    exp = payload.get("exp")

    if subject is None or email is None or token_type is None or exp is None:
        raise unauthorized

    try:
        return TokenPayload(
            sub=str(subject),
            email=email,
            exp=int(exp),
            type=str(token_type),
        )
    except (TypeError, ValueError) as exc:
        raise unauthorized from exc


def _token_payload_to_user(payload: TokenPayload, expected_type: str) -> TokenUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if payload.type != expected_type:
        raise unauthorized

    try:
        user_id = int(payload.sub)
    except (TypeError, ValueError) as exc:
        raise unauthorized from exc

    return TokenUser(user_id=user_id, email=payload.email)


def decode_access_token(token: str) -> TokenUser:
    payload = decode_token(token)
    return _token_payload_to_user(payload, expected_type="access")


def decode_refresh_token(token: str) -> TokenUser:
    payload = decode_token(token)
    return _token_payload_to_user(payload, expected_type="refresh")
