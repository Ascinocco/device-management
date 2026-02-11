from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.devices import Device, DeviceStatus
from app.devices.repository import DeviceRepository
from infra.db.models import DeviceModel


class SqlAlchemyDeviceRepository(DeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_mac(self, tenant_id: UUID, mac_address: str) -> bool:
        stmt: Select = (
            select(DeviceModel.id)
            .where(DeviceModel.tenant_id == tenant_id)
            .where(DeviceModel.mac_address == mac_address)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add(self, device: Device) -> None:
        self._session.add(self._to_model(device))
        await self._session.flush()

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        stmt = select(func.count()).select_from(DeviceModel).where(DeviceModel.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_by_tenant(self, tenant_id: UUID, limit: int, offset: int) -> list[Device]:
        stmt = (
            select(DeviceModel)
            .where(DeviceModel.tenant_id == tenant_id)
            .order_by(DeviceModel.created_at.asc(), DeviceModel.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_id(self, tenant_id: UUID, device_id: UUID) -> Device | None:
        stmt = (
            select(DeviceModel)
            .where(DeviceModel.tenant_id == tenant_id)
            .where(DeviceModel.id == device_id)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def update(self, device: Device, expected_version: int) -> bool:
        stmt = (
            update(DeviceModel)
            .where(DeviceModel.tenant_id == device.tenant_id)
            .where(DeviceModel.id == device.id)
            .where(DeviceModel.version == expected_version)
            .values(
                status=device.status.value,
                mac_address=device.mac_address,
                updated_at=device.updated_at,
                version=expected_version + 1,
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount == 1

    @staticmethod
    def _to_domain(model: DeviceModel) -> Device:
        return Device(
            id=model.id,
            tenant_id=model.tenant_id,
            mac_address=model.mac_address,
            status=DeviceStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    @staticmethod
    def _to_model(device: Device) -> DeviceModel:
        return DeviceModel(
            id=device.id,
            tenant_id=device.tenant_id,
            mac_address=device.mac_address,
            status=device.status.value,
            created_at=device.created_at,
            updated_at=device.updated_at,
            version=device.version,
        )