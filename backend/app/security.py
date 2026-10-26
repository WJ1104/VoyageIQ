"""Password hashing and signed access-token helpers."""

from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import bcrypt
import jwt


JWT_SECRET = os.getenv("JWT_SECRET", "local-development-secret-change-before-deploy")
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_LIFETIME_HOURS),
        "jti": str(uuid4()),
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> str | None:
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    user_id = claims.get("sub")
    return user_id if isinstance(user_id, str) else None
