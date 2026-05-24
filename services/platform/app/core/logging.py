import logging
import sys
import time
import uuid

from fastapi import Request

from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s service=%(name)s %(message)s",
        stream=sys.stdout,
    )


async def request_logging_middleware(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logging.getLogger("kubesage.http").info(
        "request method=%s path=%s status=%s elapsed_ms=%s trace_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        trace_id,
    )
    response.headers["x-trace-id"] = trace_id
    return response
