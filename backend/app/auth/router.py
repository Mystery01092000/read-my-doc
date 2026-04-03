from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.auth.service import AuthService
from app.common.database import get_db

router = APIRouter()


def _service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: RegisterRequest,
    svc: AuthService = Depends(_service),
) -> TokenResponse:
    return await svc.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    svc: AuthService = Depends(_service),
) -> TokenResponse:
    return await svc.login(req)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    svc: AuthService = Depends(_service),
) -> TokenResponse:
    return await svc.refresh(req.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    req: RefreshRequest,
    svc: AuthService = Depends(_service),
) -> None:
    await svc.logout(req.refresh_token)
