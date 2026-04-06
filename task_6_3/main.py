import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

load_dotenv()

MODE = os.getenv("MODE", "DEV").upper()

if MODE not in {"DEV", "PROD"}:
    raise RuntimeError("MODE must be DEV or PROD")

DOCS_USER = os.getenv("DOCS_USER", "")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "")

security = HTTPBasic()
app = FastAPI(title="Task 6.3", docs_url=None, redoc_url=None, openapi_url=None)


def verify_docs_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> None:
    if MODE != "DEV":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    if not DOCS_USER or not DOCS_PASSWORD:
        raise RuntimeError("DOCS_USER and DOCS_PASSWORD must be set in DEV mode")

    is_valid_username = secrets.compare_digest(credentials.username, DOCS_USER)
    is_valid_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/")
def root() -> dict[str, str]:
    return {"mode": MODE}


if MODE == "DEV":

    @app.get("/openapi.json", include_in_schema=False)
    def openapi_json(_: None = Depends(verify_docs_user)) -> JSONResponse:
        return JSONResponse(app.openapi())


    @app.get("/docs", include_in_schema=False)
    def docs(_: None = Depends(verify_docs_user)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} docs")

