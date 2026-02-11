"""Repository integration tests — against a real Postgres test database.

Requires DATABASE_URL pointing at a test database.
Run with: TEST_DATABASE_URL=postgresql+asyncpg://... pytest tests/test_repository.py
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.devices import Device, DeviceStatus
from infra.devices.sqlalchemy_device_repository import SqlAlchemyDeviceRepository

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://device_service:device_service@localhost:5432/device_service",
)

TENANT = uuid4()
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _device(**overrides) -> Device:
    defaults = dict(
        id=uuid4(),
        tenant_id=TENANT,
        mac_address=f"aa:bb:cc:dd:ee:{uuid4().hex[:2]}",
        status=DeviceStatus.ACTIVE,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )
    return Device(**{**defaults, **overrides})


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        async with session.begin():
            yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session: AsyncSession):
    return SqlAlchemyDeviceRepository(session)


@pytest.mark.asyncio
class TestSqlAlchemyDeviceRepository:
    async def test_add_and_get(self, repo: SqlAlchemyDeviceRepository, session: AsyncSession):
        device = _device()
        await repo.add(device)

        found = await repo.get_by_id(device.tenant_id, device.id)
        assert found is not None
        assert found.id == device.id
        assert found.mac_address == device.mac_address

    async def test_get_returns_none_for_missing(self, repo: SqlAlchemyDeviceRepository):
        result = await repo.get_by_id(TENANT, uuid4())
        assert result is None

    async def test_get_enforces_tenant_isolation(self, repo: SqlAlchemyDeviceRepository):
        device = _device()
        await repo.add(device)

        other_tenant = uuid4()
        result = await repo.get_by_id(other_tenant, device.id)
        assert result is None

    async def test_exists_by_mac(self, repo: SqlAlchemyDeviceRepository):
        device = _device()
        await repo.add(device)

        assert await repo.exists_by_mac(device.tenant_id, device.mac_address) is True
        assert await repo.exists_by_mac(device.tenant_id, "00:00:00:00:00:00") is False

    async def test_list_by_tenant_ordered(self, repo: SqlAlchemyDeviceRepository):
        d1 = _device(mac_address="aa:bb:cc:dd:ee:01", created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        d2 = _device(mac_address="aa:bb:cc:dd:ee:02", created_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
        await repo.add(d1)
        await repo.add(d2)

        devices = await repo.list_by_tenant(TENANT, limit=10, offset=0)
        assert len(devices) >= 2
        ids = [d.id for d in devices]
        assert ids.index(d1.id) < ids.index(d2.id)

    async def test_count_by_tenant(self, repo: SqlAlchemyDeviceRepository):
        await repo.add(_device())
        count = await repo.count_by_tenant(TENANT)
        assert count >= 1

    async def test_optimistic_update_success(self, repo: SqlAlchemyDeviceRepository):
        device = _device()
        await repo.add(device)

        retired = device.retire("EOL", datetime(2026, 1, 2, tzinfo=timezone.utc))
        result = await repo.update(retired, expected_version=1)
        assert result is True

    async def test_optimistic_update_conflict(self, repo: SqlAlchemyDeviceRepository):
        device = _device()
        await repo.add(device)

        retired = device.retire("EOL", datetime(2026, 1, 2, tzinfo=timezone.utc))
        result = await repo.update(retired, expected_version=99)
        assert result is False
