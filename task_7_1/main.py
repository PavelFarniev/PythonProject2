from datetime import datetime, timedelta, timezone
import os
import secrets

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Task 7.1")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-please-use-a-long-random-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALLOWED_ROLES = {"admin", "user", "guest"}


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


users_db: dict[str, dict[str, str]] = {}
resource_store = {"message": "Shared resource", "version": 1}


def find_user(username: str) -> dict[str, str] | None:
    for stored_username, user_data in users_db.items():
        if secrets.compare_digest(stored_username, username):
            return user_data
    return None


def create_access_token(username: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
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
    role = payload.get("role")

    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {"username": username, "role": role}


def require_roles(*allowed_roles: str):
    def dependency(current_user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return dependency


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest) -> dict[str, str]:
    if data.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be admin, user or guest",
        )

    if find_user(data.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    users_db[data.username] = {
        "username": data.username,
        "hashed_password": pwd_context.hash(data.password),
        "role": data.role,
    }
    return {"message": "User created"}


@app.post("/login")
def login(data: LoginRequest) -> dict[str, str]:
    user = find_user(data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not pwd_context.verify(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed",
        )

    return {
        "access_token": create_access_token(user["username"], user["role"]),
        "token_type": "bearer",
        "role": user["role"],
    }


@app.get("/protected_resource")
def protected_resource(
    current_user: dict[str, str] = Depends(require_roles("admin", "user")),
) -> dict[str, str]:
    return {
        "message": f"Access granted for {current_user['username']}",
        "role": current_user["role"],
    }


@app.post("/admin/resource")
def admin_create_resource(
    current_user: dict[str, str] = Depends(require_roles("admin")),
) -> dict[str, object]:
    resource_store["message"] = "Created by admin"
    resource_store["version"] += 1
    return {"message": "Admin action completed", "resource": resource_store, "actor": current_user["username"]}


@app.get("/user/resource")
def user_read_resource(
    current_user: dict[str, str] = Depends(require_roles("admin", "user", "guest")),
) -> dict[str, object]:
    return {"resource": resource_store, "actor": current_user["username"], "role": current_user["role"]}


class ResourceUpdate(BaseModel):
    message: str


@app.put("/user/resource")
def user_update_resource(
    payload: ResourceUpdate,
    current_user: dict[str, str] = Depends(require_roles("admin", "user")),
) -> dict[str, object]:
    resource_store["message"] = payload.message
    resource_store["version"] += 1
    return {"message": "Resource updated", "resource": resource_store, "actor": current_user["username"]}


@app.get("/guest/resource")
def guest_read_only(
    current_user: dict[str, str] = Depends(require_roles("admin", "user", "guest")),
) -> dict[str, object]:
    return {"message": "Read-only access", "resource": resource_store, "actor": current_user["username"]}
