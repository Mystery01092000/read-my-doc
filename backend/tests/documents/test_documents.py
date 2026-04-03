"""Document API tests — upload, list, get, delete."""

import io
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

REGISTER_URL = "/auth/register"
DOCS_URL = "/documents"

EMAIL = "docuser@example.com"
PASSWORD = "docpassword123"


async def _get_auth_header(client: AsyncClient) -> dict:
    resp = await client.post(REGISTER_URL, json={"email": EMAIL, "password": PASSWORD})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient) -> None:
    headers = await _get_auth_header(client)
    resp = await client.get(DOCS_URL, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
@patch("app.documents.service.process_document")
async def test_upload_txt_document(mock_task: MagicMock, client: AsyncClient, tmp_path) -> None:
    mock_task.delay = MagicMock()
    headers = await _get_auth_header(client)

    content = b"Hello, this is a test document with some content."
    files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
    resp = await client.post(DOCS_URL, headers=headers, files=files)

    assert resp.status_code == 202
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "pending"
    assert data["file_size_bytes"] == len(content)
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_upload_unsupported_extension(client: AsyncClient) -> None:
    headers = await _get_auth_header(client)
    files = {"file": ("test.docx", io.BytesIO(b"content"), "application/octet-stream")}
    resp = await client.post(DOCS_URL, headers=headers, files=files)
    assert resp.status_code == 422


@pytest.mark.asyncio
@patch("app.documents.service.process_document")
async def test_get_document(mock_task: MagicMock, client: AsyncClient, tmp_path) -> None:
    mock_task.delay = MagicMock()
    headers = await _get_auth_header(client)

    files = {"file": ("sample.txt", io.BytesIO(b"sample"), "text/plain")}
    upload_resp = await client.post(DOCS_URL, headers=headers, files=files)
    doc_id = upload_resp.json()["id"]

    resp = await client.get(f"{DOCS_URL}/{doc_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


@pytest.mark.asyncio
@patch("app.documents.service.process_document")
async def test_delete_document(mock_task: MagicMock, client: AsyncClient, tmp_path) -> None:
    mock_task.delay = MagicMock()
    headers = await _get_auth_header(client)

    files = {"file": ("todelete.txt", io.BytesIO(b"bye"), "text/plain")}
    upload_resp = await client.post(DOCS_URL, headers=headers, files=files)
    doc_id = upload_resp.json()["id"]

    del_resp = await client.delete(f"{DOCS_URL}/{doc_id}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{DOCS_URL}/{doc_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_access_other_user_document(client: AsyncClient, tmp_path) -> None:
    """User A cannot retrieve User B's document."""
    # User A uploads
    with patch("app.documents.service.process_document") as mock_task:
        mock_task.delay = MagicMock()
        a_resp = await client.post(REGISTER_URL, json={"email": "a@example.com", "password": "password123"})
        a_headers = {"Authorization": f"Bearer {a_resp.json()['access_token']}"}
        files = {"file": ("private.txt", io.BytesIO(b"secret"), "text/plain")}
        upload = await client.post(DOCS_URL, headers=a_headers, files=files)
        doc_id = upload.json()["id"]

    # User B tries to access
    b_resp = await client.post(REGISTER_URL, json={"email": "b@example.com", "password": "password123"})
    b_headers = {"Authorization": f"Bearer {b_resp.json()['access_token']}"}
    get_resp = await client.get(f"{DOCS_URL}/{doc_id}", headers=b_headers)
    assert get_resp.status_code == 404
