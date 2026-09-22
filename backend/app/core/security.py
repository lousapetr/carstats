from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


def get_current_user_email(request: Request) -> str:
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    assert isinstance(email, str)
    return email


CurrentUser = Annotated[str, Depends(get_current_user_email)]
