from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.devices.repository import DeviceRepository
from app.devices.service import DevicesApplicationService
from app.outbox.repository import OutboxRepository
from infra.db.session import get_session
from infra.devices.device_read_repository import DeviceReadRepository
from infra.devices.sqlalchemy_device_repository import SqlAlchemyDeviceRepository
from infra.outbox.sqlalchemy_outbox_repository import SqlAlchemyOutboxRepository


def get_device_repository(
    session: AsyncSession = Depends(get_session),
) -> DeviceRepository:
    return SqlAlchemyDeviceRepository(session)


def get_outbox_repository(
    session: AsyncSession = Depends(get_session),
) -> OutboxRepository:
    return SqlAlchemyOutboxRepository(session)


def get_devices_service(
    repo: DeviceRepository = Depends(get_device_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
) -> DevicesApplicationService:
    return DevicesApplicationService(repo, outbox)


def get_device_read_repository(
    session: AsyncSession = Depends(get_session),
) -> DeviceReadRepository:
    return DeviceReadRepository(session)