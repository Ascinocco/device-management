from sqlalchemy import Column, DateTime, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SagaStateModel(Base):
    __tablename__ = "saga_state"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    saga_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    current_step = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    error = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_saga_state_tenant_type", "tenant_id", "saga_type"),
    )