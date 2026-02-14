from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.contracts import ListResponse, RequestContext
from app.delivery.deps import get_request_context
from app.delivery.response_models import DataResponseModel, ListResponseModel, PageMetaModel
from app.delivery.wiring import get_device_read_repository, get_devices_service  # CHANGED
from app.devices.dto import ChangeDeviceStatusCommand, CreateDeviceCommand, DeviceView, ListDevicesQuery
from app.devices.service import DevicesApplicationService
from infra.devices.device_read_repository import DeviceReadRepository  # NEW

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


class CreateDeviceBody(BaseModel):
    mac_address: str = Field(..., min_length=1)


class ChangeStatusBody(BaseModel):
    reason: str = Field(..., min_length=1)
    expected_version: int = Field(..., ge=1)


class DeviceData(BaseModel):
    id: str
    mac_address: str
    status: str
    created_at: str
    updated_at: str
    version: int


class ProjectedDeviceData(BaseModel):
    id: str
    mac_address: str
    status: str
    owner_email: str | None = None
    created_at: str
    updated_at: str
    version: int


class DeviceResponseModel(DataResponseModel[DeviceData]):
    pass


class DeviceListResponseModel(ListResponseModel[DeviceData]):
    pass


class ProjectedDeviceListResponseModel(ListResponseModel[ProjectedDeviceData]):
    pass


@router.post("", response_model=DeviceResponseModel, status_code=201)
async def create_device(
    body: CreateDeviceBody,
    ctx: RequestContext = Depends(get_request_context),
    service: DevicesApplicationService = Depends(get_devices_service),
):
    created = await service.create(ctx, CreateDeviceCommand(mac_address=body.mac_address))
    return DeviceResponseModel(
        data=DeviceData(
            id=str(created.data.id),
            mac_address=created.data.mac_address,
            status=created.data.status.value,
            created_at=created.data.created_at.isoformat(),
            updated_at=created.data.updated_at.isoformat(),
            version=created.data.version,
        )
    )


@router.get("/projected", response_model=ProjectedDeviceListResponseModel)  # NEW
async def list_devices_projected(  # NEW
    limit: int = Query(default=50, ge=1, le=1000),  # NEW
    offset: int = Query(default=0, ge=0),  # NEW
    ctx: RequestContext = Depends(get_request_context),  # NEW
    read_repo: DeviceReadRepository = Depends(get_device_read_repository),  # NEW
):  # NEW
    data, total = await read_repo.list_by_tenant(ctx.tenant_id, limit, offset)  # NEW
    return {  # NEW
        "data": data,  # NEW
        "page": {  # NEW
            "limit": limit,  # NEW
            "offset": offset,  # NEW
            "total": total,  # NEW
            "has_next": offset + len(data) < total,  # NEW
            "order_by": ["created_at", "id"],  # NEW
        },  # NEW
    }  # NEW


@router.get("/{device_id}", response_model=DeviceResponseModel)
async def get_device(
    device_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    service: DevicesApplicationService = Depends(get_devices_service),
):
    result = await service.get(ctx, device_id)
    return DeviceResponseModel(
        data=DeviceData(
            id=str(result.data.id),
            mac_address=result.data.mac_address,
            status=result.data.status.value,
            created_at=result.data.created_at.isoformat(),
            updated_at=result.data.updated_at.isoformat(),
            version=result.data.version,
        )
    )


@router.get("", response_model=DeviceListResponseModel)
async def list_devices(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    ctx: RequestContext = Depends(get_request_context),
    service: DevicesApplicationService = Depends(get_devices_service),
):
    result: ListResponse[DeviceView] = await service.list(
        ctx,
        ListDevicesQuery(limit=limit, offset=offset),
    )
    return DeviceListResponseModel(
        data=[
            DeviceData(
                id=str(v.id),
                mac_address=v.mac_address,
                status=v.status.value,
                created_at=v.created_at.isoformat(),
                updated_at=v.updated_at.isoformat(),
                version=v.version,
            )
            for v in result.data
        ],
        page=PageMetaModel(
            limit=result.page.limit,
            offset=result.page.offset,
            total=result.page.total,
            has_next=result.page.has_next,
            order_by=result.page.order_by,
        ),
    )


@router.post("/{device_id}/retire", response_model=DeviceResponseModel, status_code=200)
async def retire_device(
    device_id: UUID,
    body: ChangeStatusBody,
    ctx: RequestContext = Depends(get_request_context),
    service: DevicesApplicationService = Depends(get_devices_service),
):
    result = await service.retire(
        ctx, device_id, ChangeDeviceStatusCommand(reason=body.reason, expected_version=body.expected_version)
    )
    return DeviceResponseModel(
        data=DeviceData(
            id=str(result.data.id),
            mac_address=result.data.mac_address,
            status=result.data.status.value,
            created_at=result.data.created_at.isoformat(),
            updated_at=result.data.updated_at.isoformat(),
            version=result.data.version,
        )
    )


@router.post("/{device_id}/activate", response_model=DeviceResponseModel, status_code=200)
async def activate_device(
    device_id: UUID,
    body: ChangeStatusBody,
    ctx: RequestContext = Depends(get_request_context),
    service: DevicesApplicationService = Depends(get_devices_service),
):
    result = await service.activate(
        ctx, device_id, ChangeDeviceStatusCommand(reason=body.reason, expected_version=body.expected_version)
    )
    return DeviceResponseModel(
        data=DeviceData(
            id=str(result.data.id),
            mac_address=result.data.mac_address,
            status=result.data.status.value,
            created_at=result.data.created_at.isoformat(),
            updated_at=result.data.updated_at.isoformat(),
            version=result.data.version,
        )
    )