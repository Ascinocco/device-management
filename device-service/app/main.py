from fastapi import FastAPI

from app.delivery.devices import router as devices_router
from app.delivery.errors import install_error_handlers

app = FastAPI(title="Device Service (Python)")

install_error_handlers(app)
app.include_router(devices_router)


@app.get("/health")
async def health():
    return {"ok": True}