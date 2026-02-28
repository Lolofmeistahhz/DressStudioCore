from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.core.config import settings


class UsernameAndPasswordProvider(AuthProvider):

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session["admin"] = username
            return response
        raise LoginFailed("Неверный логин или пароль")

    async def is_authenticated(self, request: Request) -> bool:
        return request.session.get("admin") is not None

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.session["admin"])

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response