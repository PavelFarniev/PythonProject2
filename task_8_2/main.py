from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from task_8_2.database import create_todos_table, get_db_connection

app = FastAPI(title="Task 8.2")


class TodoCreate(BaseModel):
    title: str
    description: str


class TodoUpdate(TodoCreate):
    completed: bool


class TodoResponse(TodoUpdate):
    id: int


@app.on_event("startup")
def startup() -> None:
    create_todos_table()


def get_todo_or_404(todo_id: int) -> TodoResponse:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, title, description, completed FROM todos WHERE id = ?",
        (todo_id,),
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    return TodoResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
    )


@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate) -> TodoResponse:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (payload.title, payload.description, 0),
    )
    todo_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return get_todo_or_404(todo_id)


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int) -> TodoResponse:
    return get_todo_or_404(todo_id)


@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, payload: TodoUpdate) -> TodoResponse:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE todos
        SET title = ?, description = ?, completed = ?
        WHERE id = ?
        """,
        (payload.title, payload.description, int(payload.completed), todo_id),
    )

    if cursor.rowcount == 0:
        connection.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    connection.commit()
    connection.close()
    return get_todo_or_404(todo_id)


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int) -> dict[str, str]:
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))

    if cursor.rowcount == 0:
        connection.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )

    connection.commit()
    connection.close()
    return {"message": "Todo deleted successfully"}

