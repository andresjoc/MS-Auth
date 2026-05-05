import os

from dotenv import load_dotenv


load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


AUTH_DATABASE_URL = _required_env("AUTH_DATABASE_URL")
JWT_SECRET_KEY = _required_env("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
)
APP_PORT = int(os.getenv("AUTH_SERVICE_PORT", "8002"))
FRONTEND_URL = _required_env("FRONTEND_URL")
FRONTEND_ORIGINS = [origin.strip() for origin in FRONTEND_URL.split(",") if origin.strip()]
