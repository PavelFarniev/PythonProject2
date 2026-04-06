try:
    from task_8_1.database import create_users_table
except ModuleNotFoundError:
    from database import create_users_table


if __name__ == "__main__":
    create_users_table()
    print("Table users created successfully")
