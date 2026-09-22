from collections.abc import Mapping
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.auth.oauth import google_client
from app.auth.service import is_email_allowed
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    return await google_client().authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    token = await google_client().authorize_access_token(request)
    userinfo = cast(Mapping[str, object] | None, token.get("userinfo"))
    raw_email = userinfo.get("email") if userinfo is not None else None
    if not isinstance(raw_email, str) or not raw_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Google nevrátil e-mailovou adresu"
        )

    email = raw_email.lower()
    if not is_email_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account is not authorized"
        )

    request.session["user_email"] = email
    return RedirectResponse(url="/")


@router.get("/me")
def me(request: Request) -> dict[str, str]:
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"email": email}


@router.post("/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"ok": True}
