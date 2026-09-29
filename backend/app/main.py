import mimetypes
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.attachments.router import router as attachments_router
from app.auth.router import router as auth_router
from app.car.router import router as car_router
from app.core.config import settings
from app.currency.router import router as currency_router
from app.dashboard.router import router as dashboard_router
from app.export.router import router as export_router
from app.fuel.router import router as fuel_router
from app.maintenance.router import router as maintenance_router
from app.reminders.router import router as reminders_router

# 30 days, deliberately long so the phone-installed PWA doesn't ask for a
# Google sign-in every time it's opened. Safe to keep that long because
# get_current_user_email re-checks the allowlist on every request, so a cookie
# outliving its owner's access is rejected regardless of how much life it has
# left.
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30

app = FastAPI(title="CarStats")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.session_cookie_secure,
    max_age=SESSION_MAX_AGE_SECONDS,
)

app.include_router(auth_router)
app.include_router(car_router, prefix="/api")
app.include_router(currency_router, prefix="/api")
app.include_router(fuel_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")
app.include_router(attachments_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(export_router, prefix="/api")

mimetypes.add_type("application/manifest+json", ".webmanifest")

_dist_dir = settings.frontend_dist_dir
if os.path.isdir(_dist_dir):
    _dist_dir_abs = os.path.abspath(_dist_dir)
    app.mount("/assets", StaticFiles(directory=f"{_dist_dir_abs}/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        # Real endpoints are registered above and win, so anything left under
        # these prefixes is a typo'd or retired route: 404 it rather than
        # handing the client HTML it will try to parse as JSON.
        if full_path.startswith(("api/", "auth/")):
            raise HTTPException(status_code=404, detail="Not found")

        # Serve real top-level build files (favicon, PWA manifest, service
        # worker) as-is; fall back to index.html for client-side SPA routes.
        # Path is resolved and re-checked against _dist_dir_abs to prevent
        # directory traversal via a crafted full_path (e.g. "../../etc/passwd").
        candidate = os.path.abspath(os.path.join(_dist_dir_abs, full_path))
        if full_path and candidate.startswith(_dist_dir_abs + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(f"{_dist_dir_abs}/index.html")
