from collections.abc import Mapping
from typing import Protocol, cast

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import settings


class GoogleOAuthClient(Protocol):
    """The slice of Authlib's StarletteOAuth2App that this app actually calls.

    Authlib ships no annotations and resolves registered clients through
    `BaseOAuth.__getattr__`, so `oauth.google` is untyped at the source (the
    typeshed stubs don't help — they leave `__getattr__` unannotated too).
    Declaring the two methods here is what gives the auth router real types.
    """

    async def authorize_redirect(
        self, request: Request, redirect_uri: str
    ) -> RedirectResponse: ...

    async def authorize_access_token(self, request: Request) -> Mapping[str, object]: ...


oauth = OAuth()
oauth.register(  # pyright: ignore[reportUnknownMemberType]  # unannotated upstream
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def google_client() -> GoogleOAuthClient:
    return cast(GoogleOAuthClient, oauth.google)
