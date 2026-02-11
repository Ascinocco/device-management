from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class OutboxEvent:
    id: UUID
    tenant_id: UUID
    event_type: str
    payload: dict
    created_at: datetime