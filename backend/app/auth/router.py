from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.auth.oauth import oauth
from app.auth.service import is_email_allowed
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    return await oauth.google.authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/callback")
async def callback(request: Request) -> RedirectResponse:
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if userinfo is None or not userinfo.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No email returned by Google"
        )

    email = userinfo["email"].lower()
    if not is_email_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account is not authorized"
        )

    request.session["user_email"] = email
    return RedirectResponse(url="/")


@router.get("/me")
def me(request: Request) -> dict:
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"email": email}


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}
