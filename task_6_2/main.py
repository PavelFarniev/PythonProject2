import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

app = FastAPI(title="Task 6.2")
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserBase(BaseModel):
    username: str


class User(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


fake_users_db: dict[str, UserInDB] = {}


def unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )


def get_user_from_db(username: str) -> UserInDB | None:
    for stored_username, user in fake_users_db.items():
        if secrets.compare_digest(stored_username, username):
            return user
    return None


def auth_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> UserInDB:
    user = get_user_from_db(credentials.username)

    if user is None:
        raise unauthorized_exception()

    if not pwd_context.verify(credentials.password, user.hashed_password):
        raise unauthorized_exception()

    return user


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: User) -> dict[str, str]:
    if get_user_from_db(user.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    fake_users_db[user.username] = UserInDB(
        username=user.username,
        hashed_password=pwd_context.hash(user.password),
    )
    return {"message": "User registered successfully"}


@app.get("/login")
def login(current_user: UserInDB = Depends(auth_user)) -> dict[str, str]:
    return {"message": f"Welcome, {current_user.username}!"}

