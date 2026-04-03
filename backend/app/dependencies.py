from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.common.exceptions import UnauthorizedError
from app.common.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Missing authorization header")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")
    return user_id


# Re-export get_db for convenience
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


CurrentUserId = Depends(get_current_user_id)
DbSession = Depends(db_session)
