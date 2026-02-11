from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.contracts import ConflictError, NotFoundError, ValidationError
from infra.security.jwt import AuthError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation(_req, exc: ValidationError):
        return JSONResponse(status_code=400, content={"error": "validation_error", "message": str(exc)})

    @app.exception_handler(NotFoundError)
    async def _not_found(_req, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"error": "not_found", "message": str(exc)})

    @app.exception_handler(ConflictError)
    async def _conflict(_req, exc: ConflictError):
        return JSONResponse(status_code=409, content={"error": "conflict", "message": str(exc)})

    @app.exception_handler(AuthError)
    async def _auth(_req, exc: AuthError):
        return JSONResponse(status_code=401, content={"error": "unauthorized", "message": str(exc)})