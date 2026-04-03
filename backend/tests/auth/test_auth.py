import pytest
from httpx import AsyncClient


REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
REFRESH_URL = "/auth/refresh"
LOGOUT_URL = "/auth/logout"

VALID_EMAIL = "alice@example.com"
VALID_PASSWORD = "securepass123"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": VALID_EMAIL, "password": VALID_PASSWORD}
    await client.post(REGISTER_URL, json=payload)
    response = await client.post(REGISTER_URL, json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    response = await client.post(REGISTER_URL, json={"email": "bob@example.com", "password": "short"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    response = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    response = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": "wrongpass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "anything"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    refresh_token = reg.json()["refresh_token"]

    response = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] != refresh_token  # token was rotated


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    response = await client.post(REFRESH_URL, json={"refresh_token": "not-a-valid-token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_reuse_revoked_token(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    old_refresh = reg.json()["refresh_token"]

    # Use the token once (rotates it)
    await client.post(REFRESH_URL, json={"refresh_token": old_refresh})

    # Reuse the old (now revoked) token
    response = await client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    refresh_token = reg.json()["refresh_token"]

    response = await client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    assert response.status_code == 204

    # Token should now be revoked
    response2 = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert response2.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/documents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient) -> None:
    reg = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    token = reg.json()["access_token"]

    response = await client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    # 200 or 404 accepted (route exists), not 401
    assert response.status_code != 401
