import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.attachments.router import router as attachments_router
from app.auth.router import router as auth_router
from app.car.router import router as car_router
from app.core.config import settings
from app.dashboard.router import router as dashboard_router
from app.fuel.router import router as fuel_router
from app.maintenance.router import router as maintenance_router
from app.reminders.router import router as reminders_router

app = FastAPI(title="CarStats")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")

app.include_router(auth_router)
app.include_router(car_router, prefix="/api")
app.include_router(fuel_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(attachments_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

_dist_dir = settings.frontend_dist_dir
if os.path.isdir(_dist_dir):
    app.mount("/assets", StaticFiles(directory=f"{_dist_dir}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        return FileResponse(f"{_dist_dir}/index.html")
