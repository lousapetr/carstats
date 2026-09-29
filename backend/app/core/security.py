from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.auth.service import is_email_allowed


def get_current_user_email(request: Request) -> str:
    # The allowlist is re-checked on every request, not just at login: the
    # session is a signed cookie with no server-side store, so dropping someone
    # from CARSTATS_ALLOWED_EMAILS is otherwise ignored until their cookie
    # expires. Membership in a frozenset, so it costs nothing per request.
    email = request.session.get("user_email")
    if not isinstance(email, str) or not is_email_allowed(email):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return email


CurrentUser = Annotated[str, Depends(get_current_user_email)]
