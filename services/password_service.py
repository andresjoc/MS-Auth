import hashlib

from passlib.context import CryptContext


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Pre-hash avoids bcrypt's 72-byte input limit while keeping plaintext out of storage.
    sha = hashlib.sha256(password.encode()).hexdigest()
    return password_context.hash(sha)


def verify_password(password: str, hashed: str) -> bool:
    sha = hashlib.sha256(password.encode()).hexdigest()

    if password_context.verify(sha, hashed):
        return True

    # Backward-compatible path for hashes created before the SHA-256 pre-hash change.
    return password_context.verify(password, hashed)
