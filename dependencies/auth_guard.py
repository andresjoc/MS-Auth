from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.jwt_service import decode_access_token


bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        token_user = decode_access_token(token)
    except HTTPException as exc:
        raise unauthorized from exc

    return {
        "user_id": token_user.user_id,
        "email": token_user.email,
    }
