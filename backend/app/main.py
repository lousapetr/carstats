import mimetypes
import os
from typing import override

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
from starlette.types import Scope

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

# Vite content-hashes everything under /assets/, so a changed file arrives
# under a new URL and the old one can be kept forever. The dist root keeps its
# filenames across builds (index.html, sw.js, registerSW.js, the manifest, the
# icons), so those must be revalidated instead -- "no-cache" still stores the
# file, it just forces the conditional request that FileResponse answers with a
# 304 from its ETag. Both are set explicitly because a response with no
# Cache-Control gets one invented for it: Cloudflare applies its Browser Cache
# TTL, and browsers fall back to heuristic freshness. Either can pin a stale
# service worker for hours, which strands the PWA on the previous deploy.
IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"
REVALIDATE_CACHE_CONTROL = "no-cache"

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


class _ImmutableStaticFiles(StaticFiles):
    @override
    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Cache-Control"] = IMMUTABLE_CACHE_CONTROL
        return response


_dist_dir = settings.frontend_dist_dir
if os.path.isdir(_dist_dir):
    _dist_dir_abs = os.path.abspath(_dist_dir)
    app.mount(
        "/assets",
        _ImmutableStaticFiles(directory=f"{_dist_dir_abs}/assets"),
        name="assets",
    )

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
        headers = {"Cache-Control": REVALIDATE_CACHE_CONTROL}
        if full_path and candidate.startswith(_dist_dir_abs + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate, headers=headers)
        return FileResponse(f"{_dist_dir_abs}/index.html", headers=headers)
