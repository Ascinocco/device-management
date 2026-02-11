from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.events import OutboxEvent
from app.outbox.repository import OutboxRepository
from infra.db.models import OutboxModel


class SqlAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: OutboxEvent) -> None:
        self._session.add(
            OutboxModel(
                id=event.id,
                tenant_id=event.tenant_id,
                event_type=event.event_type,
                payload=event.payload,
                created_at=event.created_at,
            )
        )
        await self._session.flush()