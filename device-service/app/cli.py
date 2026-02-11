from __future__ import annotations

import uvicorn


def dev() -> None:
    uvicorn.run(
        "app.main:app",
        reload=True,
        port=8000,
    )
