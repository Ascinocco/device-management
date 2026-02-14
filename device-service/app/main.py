from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.delivery.devices import router as devices_router
from app.delivery.errors import install_error_handlers
from infra.db.session import engine

app = FastAPI(title="Device Service (Python)")

install_error_handlers(app)
app.include_router(devices_router)


@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": str(exc)[:256]},
        )