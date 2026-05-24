from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class KubeSageError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "kubesage_error"):
        self.message = message
        self.status_code = status_code
        self.code = code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KubeSageError)
    async def handle_kubesage_error(request: Request, exc: KubeSageError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "trace_id": request.headers.get("x-trace-id"),
            },
        )
