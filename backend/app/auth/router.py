from collections.abc import Mapping
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.auth.oauth import google_client
from app.auth.service import is_email_allowed
from app.core.config import settings
from app.core.security import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    return await google_client().authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    token = await google_client().authorize_access_token(request)
    userinfo = cast(Mapping[str, object], token.get("userinfo") or {})
    raw_email = userinfo.get("email")
    if not isinstance(raw_email, str) or not raw_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Google nevrátil e-mailovou adresu"
        )

    # Google sends a JSON bool; tolerate the string form so a provider quirk
    # can't lock every account out.
    if userinfo.get("email_verified") not in (True, "true"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google účet nemá potvrzenou e-mailovou adresu",
        )

    email = raw_email.lower()
    if not is_email_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tento účet nemá přístup"
        )

    request.session["user_email"] = email
    return RedirectResponse(url="/")


@router.get("/me")
def me(user: CurrentUser) -> dict[str, str]:
    return {"email": user}


@router.post("/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}
