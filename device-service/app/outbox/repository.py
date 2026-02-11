from typing import Protocol

from app.outbox.events import OutboxEvent


class OutboxRepository(Protocol):
    async def add(self, event: OutboxEvent) -> None:
        ...