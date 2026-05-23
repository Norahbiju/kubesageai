import json
from collections.abc import AsyncGenerator


def sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def progress_stream(messages: list[str]) -> AsyncGenerator[str, None]:
    for message in messages:
        yield sse_event({"type": "progress", "message": message})
