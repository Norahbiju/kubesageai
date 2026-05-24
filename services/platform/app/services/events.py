import json
from datetime import datetime, timezone

from redis.asyncio import Redis

from app.core.config import settings


class EventBus:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def publish(self, user_id: str, event_type: str, payload: dict) -> None:
        event = {
            "type": event_type,
            "user_id": user_id,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        encoded = json.dumps(event, default=str)
        await self.redis.publish(f"events:{user_id}", encoded)
        await self.redis.xadd(
            f"stream:{user_id}",
            {
                "type": event_type,
                "user_id": user_id,
                "payload": json.dumps(payload, default=str),
                "created_at": event["created_at"],
            },
        )


events = EventBus()
