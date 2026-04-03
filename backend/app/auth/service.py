from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import RefreshTokenRepository, UserRepository
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.common.exceptions import ConflictError, UnauthorizedError
from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.config import settings


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)
        self._tokens = RefreshTokenRepository(session)

    async def register(self, req: RegisterRequest) -> TokenResponse:
        existing = await self._users.get_by_email(req.email)
        if existing is not None:
            raise ConflictError("Email already registered")

        password_hash = hash_password(req.password)
        user = await self._users.create(req.email, password_hash)

        return await self._issue_tokens(str(user.id))

    async def login(self, req: LoginRequest) -> TokenResponse:
        user = await self._users.get_by_email(req.email)
        if user is None or not verify_password(req.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        return await self._issue_tokens(str(user.id))

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        stored = await self._tokens.get_valid(refresh_token)
        if stored is None:
            raise UnauthorizedError("Refresh token has been revoked or expired")

        # Rotate: revoke old, issue new
        await self._tokens.revoke(refresh_token)
        return await self._issue_tokens(payload["sub"])

    async def logout(self, refresh_token: str) -> None:
        await self._tokens.revoke(refresh_token)

    async def _issue_tokens(self, user_id: str) -> TokenResponse:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

        import uuid
        await self._tokens.create(uuid.UUID(user_id), refresh_token, expires_at)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
