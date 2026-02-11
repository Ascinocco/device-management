from app.devices.dto import DeviceView
from app.domain.devices import Device


def to_device_view(device: Device) -> DeviceView:
    return DeviceView(
        id=device.id,
        mac_address=device.mac_address,
        status=device.status,
        created_at=device.created_at,
        updated_at=device.updated_at,
        version=device.version,
    )