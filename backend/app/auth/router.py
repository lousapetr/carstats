import logging
from collections.abc import Mapping
from typing import cast

from authlib.common.errors import AuthlibBaseError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.auth.oauth import google_client
from app.auth.service import is_email_allowed
from app.core.config import settings
from app.core.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _back_to_login(reason: str) -> RedirectResponse:
    """Send a failed sign-in back to the SPA's login screen.

    Every failure here is reached by a browser following a redirect, not by the
    API client, so an HTTPException would render a raw JSON error page with no
    way back. The reason is a short code the login screen turns into a Czech
    message; the SPA drops the parameter as soon as it has shown it.
    """
    return RedirectResponse(url=f"/?error={reason}")


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    return await google_client().authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    try:
        token = await google_client().authorize_access_token(request)
    except (AuthlibBaseError, ValueError) as exc:
        # A refreshed or bookmarked callback URL (the code is single-use), a
        # stale state after the session cookie expired, "Cancel" on the consent
        # screen, or a hiccup on Google's token endpoint all land here.
        logger.warning("OAuth callback failed: %s", exc)
        return _back_to_login("oauth")

    userinfo = cast(Mapping[str, object], token.get("userinfo") or {})
    raw_email = userinfo.get("email")
    if not isinstance(raw_email, str) or not raw_email:
        return _back_to_login("no-email")

    # Google sends a JSON bool; tolerate the string form so a provider quirk
    # can't lock every account out.
    if userinfo.get("email_verified") not in (True, "true"):
        return _back_to_login("unverified")

    email = raw_email.lower()
    if not is_email_allowed(email):
        logger.warning("Rejected sign-in from an address off the allowlist")
        return _back_to_login("not-allowed")

    request.session["user_email"] = email
    return RedirectResponse(url="/")


@router.get("/me")
def me(user: CurrentUser) -> dict[str, str]:
    return {"email": user}


@router.post("/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}
