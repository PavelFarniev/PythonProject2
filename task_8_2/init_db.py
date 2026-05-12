try:
    from task_8_2.database import create_todos_table
except ModuleNotFoundError:
    from database import create_todos_table


if __name__ == "__main__":
    create_todos_table()
    print("Table todos created successfully")

