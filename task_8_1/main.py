from fastapi import FastAPI
from pydantic import BaseModel

from task_8_1.database import create_users_table, get_db_connection

app = FastAPI(title="Task 8.1")


class User(BaseModel):
    username: str
    password: str


@app.on_event("startup")
def startup() -> None:
    create_users_table()


@app.post("/register")
def register(user: User) -> dict[str, str]:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user.username, user.password),
    )
    connection.commit()
    connection.close()
    return {"message": "User registered successfully!"}
