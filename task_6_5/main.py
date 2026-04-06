from collections import defaultdict
from datetime import datetime, timedelta, timezone
import os
import secrets
import time

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Task 6.5")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-please-use-a-long-random-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserCreate(BaseModel):
    username: str
    password: str


class RateLimiter:
    def __init__(self) -> None:
        self.storage: dict[tuple[str, str], list[float]] = defaultdict(list)

    def check(self, key: str, limit: int, period_seconds: int) -> None:
        now = time.time()
        timestamps = [value for value in self.storage[key] if now - value < period_seconds]
        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
            )
        timestamps.append(now)
        self.storage[key] = timestamps


fake_users_db: dict[str, str] = {}
rate_limiter = RateLimiter()


def get_user_hash(username: str) -> str | None:
    for stored_username, hashed_password in fake_users_db.items():
        if secrets.compare_digest(stored_username, username):
            return hashed_password
    return None


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def enforce_register_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"register:{client_ip}", limit=1, period_seconds=60)


def enforce_login_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"login:{client_ip}", limit=5, period_seconds=60)


def get_current_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing",
        )

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from error

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return username


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    _: None = Depends(enforce_register_limit),
) -> dict[str, str]:
    if get_user_hash(user.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    fake_users_db[user.username] = pwd_context.hash(user.password)
    return {"message": "New user created"}


@app.post("/login")
def login(
    user: UserCreate,
    _: None = Depends(enforce_login_limit),
) -> dict[str, str]:
    hashed_password = get_user_hash(user.username)

    if hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not pwd_context.verify(user.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed",
        )

    return {
        "access_token": create_access_token(user.username),
        "token_type": "bearer",
    }


@app.get("/protected_resource")
def protected_resource(_: str = Depends(get_current_username)) -> dict[str, str]:
    return {"message": "Access granted"}
