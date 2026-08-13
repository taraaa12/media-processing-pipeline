from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.logging import logger


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "code": "internal_error"},
    )


def not_found(processing_id: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Image with processing_id '{processing_id}' not found")
