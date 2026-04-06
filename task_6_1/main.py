import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(title="Task 6.1")
security = HTTPBasic()

VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> HTTPBasicCredentials:
    is_valid_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    is_valid_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials


@app.get("/login")
def login(_: HTTPBasicCredentials = Depends(verify_credentials)) -> dict[str, str]:
    return {"message": "You got my secret, welcome"}

