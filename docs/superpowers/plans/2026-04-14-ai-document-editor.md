# AI Document Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/documents/{id}/edit` — a two-panel AI-powered editor where users modify document content via chat, review paragraph-level diffs, accept/reject changes, and have the RAG index surgically updated.

**Architecture:** Each `ParsedPage` from initial parsing becomes a `DocumentSection`. A shadow JSON file (`{doc_id}.shadow.json`) stores the mutable section representation. `chunks.section_id` enables surgical chunk deletion on accept. Three new API endpoints, six new frontend components.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Celery, `difflib`, `httpx`, React 18, TypeScript, Tailwind CSS, Zustand-style hook state.

---

## File Map

**Create (backend):**
- `backend/alembic/versions/0006_add_section_id_to_chunks.py`
- `backend/app/documents/section_extractor.py`
- `backend/app/documents/diff_generator.py`
- `backend/app/documents/editor_schemas.py`
- `backend/app/documents/editor_service.py`
- `backend/tests/documents/test_section_extractor.py`
- `backend/tests/documents/test_diff_generator.py`
- `backend/tests/documents/test_editor_service.py`
- `backend/tests/documents/__init__.py` *(already exists)*

**Modify (backend):**
- `backend/app/documents/models.py` — add `section_id` to `Chunk`
- `backend/app/documents/chunker.py` — add `section_id` to `TextChunk`, update `chunk_pages`
- `backend/app/documents/router.py` — add 3 new routes
- `backend/tasks/document_tasks.py` — persist `section_id`; add `reindex_section` task

**Create (frontend):**
- `frontend/src/api/editor.ts`
- `frontend/src/features/editor/useEditor.ts`
- `frontend/src/features/editor/EditorPage.tsx`
- `frontend/src/features/editor/DocumentViewer.tsx`
- `frontend/src/features/editor/SectionBlock.tsx`
- `frontend/src/features/editor/DiffOverlay.tsx`
- `frontend/src/features/editor/EditPanel.tsx`

**Modify (frontend):**
- `frontend/src/types/index.ts` — add editor types
- `frontend/src/App.tsx` — add `/documents/:id/edit` route
- `frontend/src/features/documents/DocumentsPage.tsx` — add Edit button

---

## Task 1: DB Migration + SQLAlchemy Model Update

**Files:**
- Create: `backend/alembic/versions/0006_add_section_id_to_chunks.py`
- Modify: `backend/app/documents/models.py`

- [ ] **Step 1: Write the migration**

```python
# backend/alembic/versions/0006_add_section_id_to_chunks.py
"""add section_id to chunks

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-14
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chunks",
        sa.Column(
            "section_id",
            sa.String(64),
            nullable=True,
            comment="Section identifier (e.g. 'section-0'). Null for chunks ingested before this feature.",
        ),
    )
    op.create_index("ix_chunks_section_id", "chunks", ["document_id", "section_id"])


def downgrade() -> None:
    op.drop_index("ix_chunks_section_id", table_name="chunks")
    op.drop_column("chunks", "section_id")
```

- [ ] **Step 2: Add `section_id` to the `Chunk` SQLAlchemy model**

In `backend/app/documents/models.py`, add one line after `token_count`:

```python
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    section_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=False)
```

- [ ] **Step 3: Run migration**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade 0005 -> 0006, add section_id to chunks`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0006_add_section_id_to_chunks.py backend/app/documents/models.py
git commit -m "feat: add section_id column to chunks for surgical re-indexing"
```

---

## Task 2: Chunker section_id + document_tasks Persistence

**Files:**
- Modify: `backend/app/documents/chunker.py`
- Modify: `backend/tasks/document_tasks.py`
- Modify: `backend/tests/documents/test_chunker.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/documents/test_chunker.py`:

```python
def test_section_id_assigned_per_page() -> None:
    pages = [
        _page("First page content.", page_num=1),
        _page("Second page content.", page_num=2),
    ]
    chunks = chunk_pages(pages)
    page0_chunks = [c for c in chunks if c.section_id == "section-0"]
    page1_chunks = [c for c in chunks if c.section_id == "section-1"]
    assert len(page0_chunks) > 0
    assert len(page1_chunks) > 0


def test_section_id_consistent_across_splits() -> None:
    long_text = "word " * 1000  # forces multiple chunks per page
    pages = [_page(long_text, page_num=1)]
    chunks = chunk_pages(pages)
    assert all(c.section_id == "section-0" for c in chunks)
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && pytest tests/documents/test_chunker.py::test_section_id_assigned_per_page -v
```

Expected: `FAILED — AttributeError: 'TextChunk' object has no attribute 'section_id'`

- [ ] **Step 3: Update `TextChunk` dataclass and `chunk_pages` in `chunker.py`**

Replace the `TextChunk` dataclass:

```python
@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    page_number: int | None
    section_heading: str | None
    section_id: str
```

Replace `chunk_pages`:

```python
def chunk_pages(pages: list[ParsedPage]) -> list[TextChunk]:
    """Split parsed pages into overlapping chunks, assigning section_id per page."""
    all_chunks: list[TextChunk] = []
    for page_idx, page in enumerate(pages):
        section_id = f"section-{page_idx}"
        raw_chunks = _split_text(page.text)
        for text in raw_chunks:
            stripped = text.strip()
            if not stripped:
                continue
            all_chunks.append(
                TextChunk(
                    chunk_index=len(all_chunks),
                    content=stripped,
                    token_count=max(1, len(stripped) // _CHARS_PER_TOKEN),
                    page_number=page.page_number,
                    section_heading=page.section_heading,
                    section_id=section_id,
                )
            )
    return all_chunks
```

- [ ] **Step 4: Update `document_tasks.py` to persist `section_id`**

In `_process_document_async`, replace the `Chunk(...)` construction:

```python
                chunk_models = [
                    Chunk(
                        document_id=document_id,
                        chunk_index=tc.chunk_index,
                        content=tc.content,
                        embedding=emb,
                        page_number=tc.page_number,
                        section_heading=tc.section_heading,
                        token_count=tc.token_count,
                        section_id=tc.section_id,
                    )
                    for tc, emb in zip(text_chunks, embeddings)
                ]
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/documents/test_chunker.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/documents/chunker.py backend/tasks/document_tasks.py backend/tests/documents/test_chunker.py
git commit -m "feat: track section_id on chunks for surgical editor re-indexing"
```

---

## Task 3: SectionExtractor

Shadow files store section content as a JSON array at `{storage_path}.shadow.json`. Created eagerly on first `GET /sections` call for any document.

**Files:**
- Create: `backend/tests/documents/test_section_extractor.py`
- Create: `backend/app/documents/section_extractor.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/documents/test_section_extractor.py
import json
import pytest
from pathlib import Path

from app.documents.section_extractor import DocumentSection, extract_sections, patch_section


def test_txt_produces_one_section(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.txt"
    doc_file.write_text("Hello world\n\nSecond paragraph")
    sections = extract_sections(doc_file, "txt")
    assert len(sections) == 1
    assert sections[0].section_id == "section-0"
    assert "Hello world" in sections[0].content
    assert sections[0].heading is None


def test_md_produces_section_per_heading(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.md"
    doc_file.write_text("# Intro\n\nIntro text\n\n# Methods\n\nMethod text")
    sections = extract_sections(doc_file, "md")
    assert len(sections) == 2
    assert sections[0].section_id == "section-0"
    assert sections[0].heading == "Intro"
    assert sections[1].section_id == "section-1"
    assert sections[1].heading == "Methods"


def test_paragraph_blocks_split_on_double_newline(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.txt"
    doc_file.write_text("Para one\n\nPara two\n\nPara three")
    sections = extract_sections(doc_file, "txt")
    assert sections[0].paragraph_blocks == ["Para one", "Para two", "Para three"]


def test_shadow_file_created(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.txt"
    doc_file.write_text("Content")
    extract_sections(doc_file, "txt")
    shadow = Path(str(doc_file) + ".shadow.json")
    assert shadow.exists()
    data = json.loads(shadow.read_text())
    assert isinstance(data, list)
    assert data[0]["section_id"] == "section-0"


def test_shadow_reload_returns_same_sections(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.txt"
    doc_file.write_text("Content")
    first = extract_sections(doc_file, "txt")
    second = extract_sections(doc_file, "txt")
    assert len(first) == len(second)
    assert first[0].content == second[0].content


def test_patch_section_updates_shadow(tmp_path: Path) -> None:
    doc_file = tmp_path / "doc.md"
    doc_file.write_text("# Intro\n\nOriginal text\n\n# Body\n\nBody text")
    extract_sections(doc_file, "md")  # create shadow
    patch_section(doc_file, "section-0", "Updated intro text")
    sections = extract_sections(doc_file, "md")
    assert sections[0].content == "Updated intro text"
    assert sections[1].content == "Body text"  # untouched
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/documents/test_section_extractor.py -v
```

Expected: `FAILED — ModuleNotFoundError: No module named 'app.documents.section_extractor'`

- [ ] **Step 3: Implement `section_extractor.py`**

```python
# backend/app/documents/section_extractor.py
"""Converts document files to a list of editable DocumentSections via a shadow JSON file."""

import json
from dataclasses import dataclass
from pathlib import Path

from app.documents.parser import ParsedPage, parse_file


@dataclass
class DocumentSection:
    section_id: str
    section_index: int
    heading: str | None
    page_number: int | None
    content: str
    paragraph_blocks: list[str]


def _shadow_path(doc_path: Path) -> Path:
    return Path(str(doc_path) + ".shadow.json")


def _pages_to_dicts(pages: list[ParsedPage]) -> list[dict]:
    return [
        {
            "section_id": f"section-{idx}",
            "heading": page.section_heading,
            "page_number": page.page_number,
            "content": page.text,
        }
        for idx, page in enumerate(pages)
    ]


def _dict_to_section(d: dict) -> DocumentSection:
    content = d["content"]
    return DocumentSection(
        section_id=d["section_id"],
        section_index=int(d["section_id"].split("-")[1]),
        heading=d.get("heading"),
        page_number=d.get("page_number"),
        content=content,
        paragraph_blocks=[p for p in content.split("\n\n") if p.strip()],
    )


def extract_sections(doc_path: Path, file_type: str) -> list[DocumentSection]:
    """Return sections from shadow file (creating it if needed)."""
    shadow = _shadow_path(doc_path)
    if shadow.exists():
        data = json.loads(shadow.read_text(encoding="utf-8"))
        return [_dict_to_section(d) for d in data]

    pages = parse_file(doc_path, file_type)
    dicts = _pages_to_dicts(pages)
    shadow.write_text(json.dumps(dicts, ensure_ascii=False, indent=2), encoding="utf-8")
    return [_dict_to_section(d) for d in dicts]


def patch_section(doc_path: Path, section_id: str, edited_content: str) -> None:
    """Replace content for one section in the shadow file."""
    shadow = _shadow_path(doc_path)
    data: list[dict] = json.loads(shadow.read_text(encoding="utf-8"))
    updated = [
        {**d, "content": edited_content} if d["section_id"] == section_id else d
        for d in data
    ]
    shadow.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/documents/test_section_extractor.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/documents/section_extractor.py backend/tests/documents/test_section_extractor.py
git commit -m "feat: add SectionExtractor with shadow JSON files for editable document sections"
```

---

## Task 4: DiffGenerator

**Files:**
- Create: `backend/tests/documents/test_diff_generator.py`
- Create: `backend/app/documents/diff_generator.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/documents/test_diff_generator.py
import pytest
from app.documents.diff_generator import DiffBlock, generate_diff


def test_identical_text_all_unchanged() -> None:
    blocks = generate_diff("Para one\n\nPara two", "Para one\n\nPara two")
    assert all(b.type == "unchanged" for b in blocks)
    assert len(blocks) == 2


def test_full_replacement() -> None:
    blocks = generate_diff("Old text", "New text")
    types = [b.type for b in blocks]
    assert "removed" in types
    assert "added" in types
    assert "unchanged" not in types


def test_partial_replacement() -> None:
    original = "Keep this\n\nChange this"
    edited   = "Keep this\n\nNew content here"
    blocks = generate_diff(original, edited)
    unchanged = [b for b in blocks if b.type == "unchanged"]
    removed   = [b for b in blocks if b.type == "removed"]
    added     = [b for b in blocks if b.type == "added"]
    assert any("Keep this" in b.text for b in unchanged)
    assert any("Change this" in b.text for b in removed)
    assert any("New content" in b.text for b in added)


def test_deletion_produces_only_removed() -> None:
    blocks = generate_diff("Some text\n\nMore text", "")
    assert all(b.type == "removed" for b in blocks)


def test_insertion_into_empty() -> None:
    blocks = generate_diff("", "New paragraph")
    assert all(b.type == "added" for b in blocks)


def test_block_texts_cover_all_paragraphs() -> None:
    original = "A\n\nB\n\nC"
    edited   = "A\n\nX\n\nC"
    blocks = generate_diff(original, edited)
    all_texts = " ".join(b.text for b in blocks)
    assert "A" in all_texts
    assert "B" in all_texts
    assert "X" in all_texts
    assert "C" in all_texts
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/documents/test_diff_generator.py -v
```

Expected: `FAILED — ModuleNotFoundError`

- [ ] **Step 3: Implement `diff_generator.py`**

```python
# backend/app/documents/diff_generator.py
"""Paragraph-level diff using Python's difflib SequenceMatcher."""

import difflib
from dataclasses import dataclass


@dataclass(frozen=True)
class DiffBlock:
    type: str   # "unchanged" | "removed" | "added"
    text: str


def _split_paragraphs(text: str) -> list[str]:
    return [p for p in text.split("\n\n") if p.strip()]


def generate_diff(original: str, edited: str) -> list[DiffBlock]:
    """Return paragraph-level diff between original and edited text."""
    orig_paras = _split_paragraphs(original)
    edit_paras = _split_paragraphs(edited)

    if not orig_paras and not edit_paras:
        return []

    matcher = difflib.SequenceMatcher(None, orig_paras, edit_paras, autojunk=False)
    blocks: list[DiffBlock] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for para in orig_paras[i1:i2]:
                blocks.append(DiffBlock(type="unchanged", text=para))
        elif tag in ("replace", "delete"):
            for para in orig_paras[i1:i2]:
                blocks.append(DiffBlock(type="removed", text=para))
            if tag == "replace":
                for para in edit_paras[j1:j2]:
                    blocks.append(DiffBlock(type="added", text=para))
        elif tag == "insert":
            for para in edit_paras[j1:j2]:
                blocks.append(DiffBlock(type="added", text=para))

    return blocks
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/documents/test_diff_generator.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/documents/diff_generator.py backend/tests/documents/test_diff_generator.py
git commit -m "feat: add DiffGenerator for paragraph-level diff using difflib"
```

---

## Task 5: EditorService

**Files:**
- Create: `backend/tests/documents/test_editor_service.py`
- Create: `backend/app/documents/editor_service.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/documents/test_editor_service.py
import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.documents.editor_service import EditorService
from app.documents.models import Document


def _make_doc(tmp_path: Path, status: str = "ready") -> Document:
    doc_id = uuid.uuid4()
    user_id = uuid.uuid4()
    path = tmp_path / f"{doc_id}.txt"
    path.write_text("Introduction text\n\nMore content here")
    doc = Document(
        id=doc_id,
        user_id=user_id,
        filename="test.txt",
        file_type="txt",
        file_size_bytes=path.stat().st_size,
        storage_path=str(path),
        status=status,
    )
    return doc


@pytest.mark.asyncio
async def test_get_sections_returns_sections(tmp_path: Path) -> None:
    doc = _make_doc(tmp_path)
    mock_session = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=doc)

    with patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo):
        svc = EditorService(mock_session)
        result = await svc.get_sections(doc.id, doc.user_id)

    assert len(result.sections) == 1
    assert result.sections[0].section_id == "section-0"


@pytest.mark.asyncio
async def test_get_sections_raises_404_for_missing_doc() -> None:
    from app.common.exceptions import NotFoundError
    mock_session = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=None)

    with patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo):
        svc = EditorService(mock_session)
        with pytest.raises(NotFoundError):
            await svc.get_sections(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_get_sections_raises_409_when_processing(tmp_path: Path) -> None:
    from app.common.exceptions import ConflictError
    doc = _make_doc(tmp_path, status="processing")
    mock_session = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=doc)

    with patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo):
        svc = EditorService(mock_session)
        with pytest.raises(ConflictError):
            await svc.get_sections(doc.id, doc.user_id)


@pytest.mark.asyncio
async def test_propose_edit_returns_diff(tmp_path: Path) -> None:
    doc = _make_doc(tmp_path)
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(fetchone=MagicMock(return_value=None)))
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=doc)

    with (
        patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo),
        patch("app.documents.editor_service._call_editor_llm", new_callable=AsyncMock) as mock_llm,
    ):
        mock_llm.return_value = "Concise introduction"
        svc = EditorService(mock_session)
        result = await svc.propose_edit(doc.id, doc.user_id, "make it concise", None)

    assert result.section_id == "section-0"
    assert result.edited_paragraphs == ["Concise introduction"]
    assert any(b.type in ("added", "removed", "unchanged") for b in result.diff)


@pytest.mark.asyncio
async def test_propose_edit_rejects_empty_llm_response(tmp_path: Path) -> None:
    from app.common.exceptions import UnprocessableError
    doc = _make_doc(tmp_path)
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(fetchone=MagicMock(return_value=None)))
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=doc)

    with (
        patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo),
        patch("app.documents.editor_service._call_editor_llm", new_callable=AsyncMock) as mock_llm,
    ):
        mock_llm.return_value = "   "
        svc = EditorService(mock_session)
        with pytest.raises(UnprocessableError):
            await svc.propose_edit(doc.id, doc.user_id, "rewrite", None)


@pytest.mark.asyncio
async def test_accept_edit_patches_shadow_and_enqueues_task(tmp_path: Path) -> None:
    doc = _make_doc(tmp_path)
    mock_session = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=doc)
    mock_repo.set_status = AsyncMock()

    mock_task = MagicMock()
    mock_task.id = "celery-task-abc"

    with (
        patch("app.documents.editor_service.DocumentRepository", return_value=mock_repo),
        patch("app.documents.editor_service.reindex_section") as mock_reindex,
    ):
        mock_reindex.delay = MagicMock(return_value=mock_task)
        svc = EditorService(mock_session)
        # First call extract_sections to create shadow
        await svc.get_sections(doc.id, doc.user_id)
        result = await svc.accept_edit(doc.id, doc.user_id, "section-0", ["New content"])

    assert result.status == "reindexing"
    assert result.task_id == "celery-task-abc"
    mock_repo.set_status.assert_called_once_with(doc.id, "processing")
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/documents/test_editor_service.py -v
```

Expected: `FAILED — ModuleNotFoundError: No module named 'app.documents.editor_service'`

- [ ] **Step 3: Implement `editor_service.py`**

```python
# backend/app/documents/editor_service.py
"""Orchestrates section loading, LLM editing, diff generation, and re-indexing dispatch."""

import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.config import settings
from app.documents.diff_generator import DiffBlock, generate_diff
from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.documents.section_extractor import DocumentSection, extract_sections, patch_section
from app.rag.embedder import embed_query

EDITOR_SYSTEM_PROMPT = (
    "You are a document editor. You will receive a section of text and an editing instruction. "
    "Return ONLY the edited version of the section with the instruction applied. "
    "Preserve all headings, formatting, and content not targeted by the instruction. "
    "Do not add commentary or explanations — return only the edited text."
)

_DELETE_SENTINEL = "__DELETE_SECTION__"


# ── Response dataclasses ──────────────────────────────────────────────────────

@dataclass
class DiffBlockSchema:
    type: str
    text: str


@dataclass
class SectionsResponse:
    document_id: str
    filename: str
    file_type: str
    sections: list[DocumentSection]


@dataclass
class EditProposalResponse:
    section_id: str
    heading: str | None
    original_paragraphs: list[str]
    edited_paragraphs: list[str]
    diff: list[DiffBlockSchema]


@dataclass
class AcceptEditResponse:
    document_id: str
    section_id: str
    status: str
    task_id: str


# ── Service ───────────────────────────────────────────────────────────────────

class EditorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._doc_repo = DocumentRepository(session)

    async def get_sections(self, document_id: uuid.UUID, user_id: uuid.UUID) -> SectionsResponse:
        doc = await self._doc_repo.get(document_id, user_id)
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        if doc.status in ("pending", "processing"):
            raise ConflictError("Document is not ready for editing")

        sections = extract_sections(Path(doc.storage_path), doc.file_type)
        return SectionsResponse(
            document_id=str(doc.id),
            filename=doc.filename,
            file_type=doc.file_type,
            sections=sections,
        )

    async def propose_edit(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        instruction: str,
        section_id: str | None,
    ) -> EditProposalResponse:
        doc = await self._doc_repo.get(document_id, user_id)
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        if doc.status in ("pending", "processing"):
            raise ConflictError("Document is not ready for editing")

        sections = extract_sections(Path(doc.storage_path), doc.file_type)
        target = await _identify_section(sections, section_id, instruction, document_id, self._session)

        original_paras = [p for p in target.content.split("\n\n") if p.strip()]

        # Handle delete sentinel
        if instruction == _DELETE_SENTINEL:
            diff = [DiffBlockSchema(type="removed", text=p) for p in original_paras]
            return EditProposalResponse(
                section_id=target.section_id,
                heading=target.heading,
                original_paragraphs=original_paras,
                edited_paragraphs=[],
                diff=diff,
            )

        user_message = f"INSTRUCTION: {instruction}\n\nSECTION:\n{target.content}"
        edited_text = await _call_editor_llm(EDITOR_SYSTEM_PROMPT, user_message)

        if not edited_text.strip():
            raise UnprocessableError("LLM returned an empty edit — try rephrasing your instruction")

        original_len = len(target.content)
        if original_len > 0:
            ratio = len(edited_text) / original_len
            if ratio < 0.05 or ratio > 10.0:
                raise UnprocessableError("LLM edit length is implausible — try rephrasing your instruction")

        edited_paras = [p for p in edited_text.split("\n\n") if p.strip()]
        raw_diff = generate_diff(target.content, edited_text)
        diff = [DiffBlockSchema(type=b.type, text=b.text) for b in raw_diff]

        return EditProposalResponse(
            section_id=target.section_id,
            heading=target.heading,
            original_paragraphs=original_paras,
            edited_paragraphs=edited_paras,
            diff=diff,
        )

    async def accept_edit(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        section_id: str,
        edited_paragraphs: list[str],
    ) -> AcceptEditResponse:
        doc = await self._doc_repo.get(document_id, user_id)
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        if doc.status in ("pending", "processing"):
            raise ConflictError("Document is currently being processed — try again shortly")

        edited_content = "\n\n".join(edited_paragraphs)
        patch_section(Path(doc.storage_path), section_id, edited_content)
        await self._doc_repo.set_status(document_id, "processing")

        from tasks.document_tasks import reindex_section
        task = reindex_section.delay(str(document_id), section_id)

        return AcceptEditResponse(
            document_id=str(document_id),
            section_id=section_id,
            status="reindexing",
            task_id=task.id,
        )


# ── Section identification ────────────────────────────────────────────────────

async def _identify_section(
    sections: list[DocumentSection],
    section_id: str | None,
    instruction: str,
    document_id: uuid.UUID,
    session: AsyncSession,
) -> DocumentSection:
    if section_id is not None:
        for s in sections:
            if s.section_id == section_id:
                return s
        raise NotFoundError("Section", section_id)

    query_embedding = embed_query(instruction)
    result = await session.execute(
        text("""
            SELECT section_id
            FROM chunks
            WHERE document_id = :doc_id
              AND section_id IS NOT NULL
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT 1
        """),
        {"doc_id": str(document_id), "query_vec": str(query_embedding)},
    )
    row = result.fetchone()
    if row and row[0]:
        for s in sections:
            if s.section_id == row[0]:
                return s

    return sections[0]


# ── LLM dispatch ──────────────────────────────────────────────────────────────

async def _call_editor_llm(system_prompt: str, user_message: str) -> str:
    if settings.llm_provider == "openai":
        return await _call_openai(system_prompt, user_message)
    if settings.llm_provider == "groq":
        return await _call_groq(system_prompt, user_message)
    return await _call_ollama(system_prompt, user_message)


async def _call_ollama(system_prompt: str, user_message: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def _call_openai(system_prompt: str, user_message: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _call_groq(system_prompt: str, user_message: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/documents/test_editor_service.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/documents/editor_service.py backend/tests/documents/test_editor_service.py
git commit -m "feat: add EditorService with section loading, LLM edit, diff, and accept"
```

---

## Task 6: Celery `reindex_section` Task

**Files:**
- Modify: `backend/tasks/document_tasks.py`

- [ ] **Step 1: Add `reindex_section` task at the bottom of `document_tasks.py`**

```python
@celery_app.task(bind=True, name="tasks.reindex_section", max_retries=3, default_retry_delay=30, ignore_result=True)
def reindex_section(self, document_id: str, section_id: str) -> None:
    try:
        asyncio.run(_reindex_section_async(document_id, section_id))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _reindex_section_async(document_id_str: str, section_id: str) -> None:
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings
    from app.documents.chunker import chunk_pages
    from app.documents.models import Chunk, Document
    from app.documents.parser import ParsedPage
    from app.documents.repository import DocumentRepository
    from app.documents.section_extractor import extract_sections
    from app.rag.embedder import embed_texts

    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    document_id = uuid.UUID(document_id_str)

    async with session_factory() as session:
        async with session.begin():
            result = await session.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc is None:
                return

            repo = DocumentRepository(session)
            try:
                # Load edited section from shadow file
                from pathlib import Path
                sections = extract_sections(Path(doc.storage_path), doc.file_type)
                target = next((s for s in sections if s.section_id == section_id), None)
                if target is None:
                    await repo.set_status(document_id, "failed", error_message=f"Section {section_id} not found in shadow file")
                    return

                # Delete old chunks for this section
                await session.execute(
                    delete(Chunk).where(
                        Chunk.document_id == document_id,
                        Chunk.section_id == section_id,
                    )
                )

                # If edited content is empty, just remove (delete section)
                if not target.content.strip():
                    await repo.set_status(document_id, "ready")
                    return

                # Re-chunk and re-embed
                page = ParsedPage(
                    page_number=target.page_number,
                    section_heading=target.heading,
                    text=target.content,
                )
                text_chunks = chunk_pages([page])

                # Assign new chunk_index values (append after existing)
                count_result = await session.execute(
                    __import__("sqlalchemy", fromlist=["func", "select"]).select(
                        __import__("sqlalchemy", fromlist=["func"]).func.count()
                    ).where(Chunk.document_id == document_id)
                )
                existing_count = count_result.scalar_one()

                texts = [c.content for c in text_chunks]
                embeddings: list[list[float]] = []
                for i in range(0, len(texts), 32):
                    embeddings.extend(embed_texts(texts[i : i + 32]))

                new_chunks = [
                    Chunk(
                        document_id=document_id,
                        chunk_index=existing_count + idx,
                        content=tc.content,
                        embedding=emb,
                        page_number=tc.page_number,
                        section_heading=tc.section_heading,
                        token_count=tc.token_count,
                        section_id=tc.section_id,
                    )
                    for idx, (tc, emb) in enumerate(zip(text_chunks, embeddings))
                ]
                session.add_all(new_chunks)
                await session.flush()

                # Rebuild tsvector for new chunks
                await session.execute(
                    __import__("sqlalchemy", fromlist=["text"]).text(
                        "UPDATE chunks SET tsv = to_tsvector('english', content) "
                        "WHERE document_id = :doc_id AND section_id = :section_id"
                    ),
                    {"doc_id": document_id, "section_id": section_id},
                )

                # Recalculate total tokens
                token_result = await session.execute(
                    __import__("sqlalchemy", fromlist=["func", "select"]).select(
                        __import__("sqlalchemy", fromlist=["func"]).func.sum(Chunk.token_count)
                    ).where(Chunk.document_id == document_id)
                )
                total_tokens = token_result.scalar_one() or 0
                await repo.set_status(document_id, "ready", tokens_embedded=total_tokens)

            except Exception as exc:
                await repo.set_status(document_id, "failed", error_message=str(exc)[:500])
                raise

    await engine.dispose()
```

- [ ] **Step 2: Fix the import ugliness** — replace the `__import__` calls with proper top-level imports. At the top of `_reindex_section_async`, add:

```python
    from sqlalchemy import delete, func, select, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    # (move all from-imports here, keeping the function body clean)
```

Then replace the body to use `func.count()`, `func.sum()`, `text(...)` directly without `__import__`.

- [ ] **Step 3: Run existing document task tests to confirm no regression**

```bash
cd backend && pytest tests/documents/ -v -k "not editor"
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add backend/tasks/document_tasks.py
git commit -m "feat: add reindex_section Celery task for surgical chunk re-indexing on edit accept"
```

---

## Task 7: API Routes + Pydantic Schemas

**Files:**
- Create: `backend/app/documents/editor_schemas.py`
- Modify: `backend/app/documents/router.py`

- [ ] **Step 1: Write failing API tests**

Add to `backend/tests/documents/test_documents.py` (at the bottom, after existing tests):

```python
# ── Editor endpoint tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sections_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/documents/00000000-0000-0000-0000-000000000001/sections")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_post_edit_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/documents/00000000-0000-0000-0000-000000000001/edit",
        json={"instruction": "test", "section_id": None},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_section_requires_auth(client: AsyncClient) -> None:
    response = await client.put(
        "/documents/00000000-0000-0000-0000-000000000001/sections/section-0",
        json={"edited_paragraphs": ["text"]},
    )
    assert response.status_code == 401
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/documents/test_documents.py::test_get_sections_requires_auth -v
```

Expected: `FAILED — 404 Not Found` (route doesn't exist yet)

- [ ] **Step 3: Create `editor_schemas.py`**

```python
# backend/app/documents/editor_schemas.py
"""Pydantic request/response models for the editor endpoints."""

from pydantic import BaseModel, Field


class DiffBlockResponse(BaseModel):
    type: str   # "unchanged" | "removed" | "added"
    text: str


class DocumentSectionResponse(BaseModel):
    section_id: str
    section_index: int
    heading: str | None
    page_number: int | None
    content: str
    paragraph_blocks: list[str]


class SectionsResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    sections: list[DocumentSectionResponse]


class EditRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    section_id: str | None = None


class EditProposalResponse(BaseModel):
    section_id: str
    heading: str | None
    original_paragraphs: list[str]
    edited_paragraphs: list[str]
    diff: list[DiffBlockResponse]


class AcceptEditRequest(BaseModel):
    edited_paragraphs: list[str]


class AcceptEditResponse(BaseModel):
    document_id: str
    section_id: str
    status: str
    task_id: str
```

- [ ] **Step 4: Add 3 new routes to `router.py`**

Add these imports at the top of `backend/app/documents/router.py`:

```python
from app.documents.editor_schemas import (
    AcceptEditRequest,
    AcceptEditResponse,
    EditProposalResponse,
    EditRequest,
    SectionsResponse,
)
from app.documents.editor_service import EditorService
```

Add a second service factory and three routes at the bottom:

```python
def _editor_service(session: AsyncSession = Depends(get_db)) -> EditorService:
    return EditorService(session)


@router.get("/{document_id}/sections", response_model=SectionsResponse)
async def get_sections(
    document_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    svc: EditorService = Depends(_editor_service),
) -> SectionsResponse:
    result = await svc.get_sections(document_id, uuid.UUID(user_id))
    return SectionsResponse(
        document_id=result.document_id,
        filename=result.filename,
        file_type=result.file_type,
        sections=[
            {
                "section_id": s.section_id,
                "section_index": s.section_index,
                "heading": s.heading,
                "page_number": s.page_number,
                "content": s.content,
                "paragraph_blocks": s.paragraph_blocks,
            }
            for s in result.sections
        ],
    )


@router.post("/{document_id}/edit", response_model=EditProposalResponse)
async def propose_edit(
    document_id: uuid.UUID,
    body: EditRequest,
    user_id: str = Depends(get_current_user_id),
    svc: EditorService = Depends(_editor_service),
) -> EditProposalResponse:
    result = await svc.propose_edit(document_id, uuid.UUID(user_id), body.instruction, body.section_id)
    return EditProposalResponse(
        section_id=result.section_id,
        heading=result.heading,
        original_paragraphs=result.original_paragraphs,
        edited_paragraphs=result.edited_paragraphs,
        diff=[{"type": b.type, "text": b.text} for b in result.diff],
    )


@router.put("/{document_id}/sections/{section_id}", response_model=AcceptEditResponse)
async def accept_edit(
    document_id: uuid.UUID,
    section_id: str,
    body: AcceptEditRequest,
    user_id: str = Depends(get_current_user_id),
    svc: EditorService = Depends(_editor_service),
) -> AcceptEditResponse:
    result = await svc.accept_edit(document_id, uuid.UUID(user_id), section_id, body.edited_paragraphs)
    return AcceptEditResponse(
        document_id=result.document_id,
        section_id=result.section_id,
        status=result.status,
        task_id=result.task_id,
    )
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/documents/test_documents.py -v -k "auth"
```

Expected: all PASS (401 for unauthenticated requests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/documents/editor_schemas.py backend/app/documents/router.py
git commit -m "feat: add GET /sections, POST /edit, PUT /sections/{id} editor endpoints"
```

---

## Task 8: Frontend Types + API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/editor.ts`

- [ ] **Step 1: Add editor types to `frontend/src/types/index.ts`**

Append after the `PaginatedResponse` interface:

```typescript
// ── Editor ────────────────────────────────────────────────────────────────────

export type DiffBlockType = 'unchanged' | 'removed' | 'added';

export interface DiffBlock {
  type: DiffBlockType;
  text: string;
}

export interface DocumentSection {
  sectionId: string;
  sectionIndex: number;
  heading: string | null;
  pageNumber: number | null;
  content: string;
  paragraphBlocks: string[];
}

export interface SectionsResponse {
  documentId: string;
  filename: string;
  fileType: string;
  sections: DocumentSection[];
}

export interface EditProposalResponse {
  sectionId: string;
  heading: string | null;
  originalParagraphs: string[];
  editedParagraphs: string[];
  diff: DiffBlock[];
}

export interface AcceptEditResponse {
  documentId: string;
  sectionId: string;
  status: string;
  taskId: string;
}
```

- [ ] **Step 2: Create `frontend/src/api/editor.ts`**

```typescript
import type {
  AcceptEditResponse,
  EditProposalResponse,
  SectionsResponse,
} from '@/types';
import { createApiClient } from './client';
import { useAuthStore } from '@/store/useAuthStore';

function client() {
  return createApiClient(() => useAuthStore.getState().accessToken);
}

function toSection(raw: Record<string, unknown>) {
  return {
    sectionId: raw.section_id as string,
    sectionIndex: raw.section_index as number,
    heading: raw.heading as string | null,
    pageNumber: raw.page_number as number | null,
    content: raw.content as string,
    paragraphBlocks: raw.paragraph_blocks as string[],
  };
}

function toDiffBlock(raw: Record<string, unknown>) {
  return {
    type: raw.type as 'unchanged' | 'removed' | 'added',
    text: raw.text as string,
  };
}

export const editorApi = {
  getSections: async (documentId: string): Promise<SectionsResponse> => {
    const { data } = await client().get(`/documents/${documentId}/sections`);
    return {
      documentId: data.document_id,
      filename: data.filename,
      fileType: data.file_type,
      sections: (data.sections as Record<string, unknown>[]).map(toSection),
    };
  },

  proposeEdit: async (
    documentId: string,
    instruction: string,
    sectionId: string | null = null,
  ): Promise<EditProposalResponse> => {
    const { data } = await client().post(`/documents/${documentId}/edit`, {
      instruction,
      section_id: sectionId,
    });
    return {
      sectionId: data.section_id,
      heading: data.heading,
      originalParagraphs: data.original_paragraphs,
      editedParagraphs: data.edited_paragraphs,
      diff: (data.diff as Record<string, unknown>[]).map(toDiffBlock),
    };
  },

  acceptEdit: async (
    documentId: string,
    sectionId: string,
    editedParagraphs: string[],
  ): Promise<AcceptEditResponse> => {
    const { data } = await client().put(
      `/documents/${documentId}/sections/${sectionId}`,
      { edited_paragraphs: editedParagraphs },
    );
    return {
      documentId: data.document_id,
      sectionId: data.section_id,
      status: data.status,
      taskId: data.task_id,
    };
  },
};

export const QUICK_ACTIONS = [
  { label: 'Fix Grammar', instruction: 'Fix grammar and spelling errors only. Do not change meaning or structure.' },
  { label: 'Summarize', instruction: 'Summarize this section to 30% of its current length, preserving key points.' },
  { label: 'Expand', instruction: 'Expand this section with more detail and supporting explanation.' },
  { label: 'Delete', instruction: '__DELETE_SECTION__' },
] as const;
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/editor.ts
git commit -m "feat: add editor types and API client"
```

---

## Task 9: `useEditor` Hook

**Files:**
- Create: `frontend/src/features/editor/useEditor.ts`

- [ ] **Step 1: Create the hook**

```typescript
// frontend/src/features/editor/useEditor.ts
import { useCallback, useState } from 'react';
import { editorApi } from '@/api/editor';
import type {
  DiffBlock,
  DocumentSection,
  SectionsResponse,
} from '@/types';

export type EditorStatus = 'idle' | 'loading' | 'diff-ready' | 'reindexing';

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
}

export interface PendingDiff {
  sectionId: string;
  diff: DiffBlock[];
  editedParagraphs: string[];
}

export interface EditorState {
  documentId: string;
  filename: string;
  sections: DocumentSection[];
  pendingDiff: PendingDiff | null;
  status: EditorStatus;
  chatHistory: ChatMessage[];
  error: string | null;
}

export function useEditor(documentId: string) {
  const [state, setState] = useState<EditorState>({
    documentId,
    filename: '',
    sections: [],
    pendingDiff: null,
    status: 'idle',
    chatHistory: [],
    error: null,
  });

  const loadSections = useCallback(async () => {
    setState(s => ({ ...s, status: 'loading', error: null }));
    try {
      const result: SectionsResponse = await editorApi.getSections(documentId);
      setState(s => ({
        ...s,
        filename: result.filename,
        sections: result.sections,
        status: 'idle',
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load document sections';
      setState(s => ({ ...s, status: 'idle', error: message }));
    }
  }, [documentId]);

  const sendInstruction = useCallback(
    async (instruction: string, sectionId: string | null = null) => {
      setState(s => ({
        ...s,
        status: 'loading',
        error: null,
        chatHistory: [...s.chatHistory, { role: 'user', text: instruction }],
      }));
      try {
        const proposal = await editorApi.proposeEdit(documentId, instruction, sectionId);
        setState(s => ({
          ...s,
          status: 'diff-ready',
          pendingDiff: {
            sectionId: proposal.sectionId,
            diff: proposal.diff,
            editedParagraphs: proposal.editedParagraphs,
          },
          chatHistory: [
            ...s.chatHistory,
            { role: 'assistant', text: `Proposed edit to "${proposal.heading ?? proposal.sectionId}". Review the diff and accept or reject.` },
          ],
        }));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Edit failed';
        setState(s => ({
          ...s,
          status: 'idle',
          error: message,
          chatHistory: [...s.chatHistory, { role: 'assistant', text: `Error: ${message}` }],
        }));
      }
    },
    [documentId],
  );

  const acceptDiff = useCallback(async () => {
    if (!state.pendingDiff) return;
    const { sectionId, editedParagraphs } = state.pendingDiff;
    setState(s => ({ ...s, status: 'reindexing', pendingDiff: null }));
    try {
      await editorApi.acceptEdit(documentId, sectionId, editedParagraphs);
      // Optimistically update the section content in state
      setState(s => ({
        ...s,
        sections: s.sections.map(sec =>
          sec.sectionId === sectionId
            ? { ...sec, content: editedParagraphs.join('\n\n'), paragraphBlocks: editedParagraphs }
            : sec,
        ),
        chatHistory: [...s.chatHistory, { role: 'assistant', text: 'Edit accepted. Re-indexing in background...' }],
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Accept failed';
      setState(s => ({ ...s, status: 'idle', error: message }));
    }
  }, [documentId, state.pendingDiff]);

  const rejectDiff = useCallback(() => {
    setState(s => ({
      ...s,
      pendingDiff: null,
      status: 'idle',
      chatHistory: [...s.chatHistory, { role: 'assistant', text: 'Edit rejected.' }],
    }));
  }, []);

  return { state, loadSections, sendInstruction, acceptDiff, rejectDiff };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/editor/useEditor.ts
git commit -m "feat: add useEditor hook for editor page state management"
```

---

## Task 10: DiffOverlay + SectionBlock Components

**Files:**
- Create: `frontend/src/features/editor/DiffOverlay.tsx`
- Create: `frontend/src/features/editor/SectionBlock.tsx`

- [ ] **Step 1: Create `DiffOverlay.tsx`**

```tsx
// frontend/src/features/editor/DiffOverlay.tsx
import type { DiffBlock } from '@/types';

interface DiffOverlayProps {
  diff: DiffBlock[];
  onAccept: () => void;
  onReject: () => void;
}

export function DiffOverlay({ diff, onAccept, onReject }: DiffOverlayProps) {
  return (
    <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-900 overflow-hidden">
      <div className="px-3 py-2 text-xs text-zinc-400 border-b border-zinc-700 font-mono">
        PROPOSED CHANGES
      </div>
      <div className="p-3 space-y-1 max-h-64 overflow-y-auto font-mono text-sm">
        {diff.map((block, idx) => (
          <div
            key={idx}
            className={
              block.type === 'removed'
                ? 'bg-red-950/50 text-red-300 line-through px-2 py-1 rounded'
                : block.type === 'added'
                ? 'bg-emerald-950/50 text-emerald-300 px-2 py-1 rounded'
                : 'text-zinc-400 px-2 py-1'
            }
          >
            <span className="mr-2 select-none opacity-50">
              {block.type === 'removed' ? '−' : block.type === 'added' ? '+' : ' '}
            </span>
            {block.text}
          </div>
        ))}
      </div>
      <div className="flex gap-2 px-3 py-2 border-t border-zinc-700">
        <button
          onClick={onAccept}
          className="flex-1 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
        >
          ✓ Accept
        </button>
        <button
          onClick={onReject}
          className="flex-1 py-1.5 rounded bg-zinc-700 hover:bg-zinc-600 text-white text-sm font-medium transition-colors"
        >
          ✗ Reject
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `SectionBlock.tsx`**

```tsx
// frontend/src/features/editor/SectionBlock.tsx
import type { DiffBlock, DocumentSection } from '@/types';
import { DiffOverlay } from './DiffOverlay';

interface SectionBlockProps {
  section: DocumentSection;
  isActive: boolean;
  pendingDiff: DiffBlock[] | null;
  onAccept: () => void;
  onReject: () => void;
}

export function SectionBlock({
  section,
  isActive,
  pendingDiff,
  onAccept,
  onReject,
}: SectionBlockProps) {
  return (
    <div
      id={`section-${section.sectionIndex}`}
      className={`p-4 rounded-lg border transition-colors ${
        isActive
          ? 'border-blue-500/50 bg-blue-950/20'
          : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700'
      }`}
    >
      {section.heading && (
        <h3 className="text-sm font-semibold text-zinc-200 mb-2">{section.heading}</h3>
      )}
      {section.pageNumber != null && (
        <div className="text-xs text-zinc-500 mb-2">Page {section.pageNumber}</div>
      )}
      {pendingDiff ? (
        <DiffOverlay diff={pendingDiff} onAccept={onAccept} onReject={onReject} />
      ) : (
        <div className="space-y-2">
          {section.paragraphBlocks.map((para, idx) => (
            <p key={idx} className="text-sm text-zinc-300 leading-relaxed">
              {para}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/editor/DiffOverlay.tsx frontend/src/features/editor/SectionBlock.tsx
git commit -m "feat: add DiffOverlay and SectionBlock editor components"
```

---

## Task 11: DocumentViewer

**Files:**
- Create: `frontend/src/features/editor/DocumentViewer.tsx`

- [ ] **Step 1: Create `DocumentViewer.tsx`**

```tsx
// frontend/src/features/editor/DocumentViewer.tsx
import { useEffect, useRef } from 'react';
import type { DiffBlock, DocumentSection } from '@/types';
import { SectionBlock } from './SectionBlock';

interface DocumentViewerProps {
  sections: DocumentSection[];
  activeSectionId: string | null;
  pendingDiff: { sectionId: string; diff: DiffBlock[] } | null;
  onAccept: () => void;
  onReject: () => void;
}

export function DocumentViewer({
  sections,
  activeSectionId,
  pendingDiff,
  onAccept,
  onReject,
}: DocumentViewerProps) {
  const activeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (activeSectionId) {
      const el = document.getElementById(`section-${sections.find(s => s.sectionId === activeSectionId)?.sectionIndex}`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [activeSectionId, sections]);

  if (sections.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
        No sections found in this document.
      </div>
    );
  }

  return (
    <div ref={activeRef} className="h-full overflow-y-auto p-4 space-y-3">
      {sections.map(section => (
        <SectionBlock
          key={section.sectionId}
          section={section}
          isActive={section.sectionId === activeSectionId}
          pendingDiff={pendingDiff?.sectionId === section.sectionId ? pendingDiff.diff : null}
          onAccept={onAccept}
          onReject={onReject}
        />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/editor/DocumentViewer.tsx
git commit -m "feat: add DocumentViewer left-panel component with scroll-to-active"
```

---

## Task 12: EditPanel + EditorPage + Route + Edit Button

**Files:**
- Create: `frontend/src/features/editor/EditPanel.tsx`
- Create: `frontend/src/features/editor/EditorPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/features/documents/DocumentsPage.tsx`

- [ ] **Step 1: Create `EditPanel.tsx`**

```tsx
// frontend/src/features/editor/EditPanel.tsx
import { useRef, useState } from 'react';
import { QUICK_ACTIONS } from '@/api/editor';
import type { ChatMessage } from './useEditor';

interface EditPanelProps {
  chatHistory: ChatMessage[];
  status: 'idle' | 'loading' | 'diff-ready' | 'reindexing';
  onSend: (instruction: string) => void;
  error: string | null;
}

export function EditPanel({ chatHistory, status, onSend, error }: EditPanelProps) {
  const [input, setInput] = useState('');
  const [translateLang, setTranslateLang] = useState('');
  const [showTranslatePrompt, setShowTranslatePrompt] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || status === 'loading' || status === 'reindexing') return;
    onSend(trimmed);
    setInput('');
  };

  const handleQuickAction = (instruction: string) => {
    if (instruction === 'TRANSLATE_PROMPT') {
      setShowTranslatePrompt(true);
      return;
    }
    onSend(instruction);
  };

  const handleTranslateSubmit = () => {
    if (!translateLang.trim()) return;
    onSend(`Translate this section to ${translateLang.trim()}.`);
    setTranslateLang('');
    setShowTranslatePrompt(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Quick actions */}
      <div className="flex flex-wrap gap-1.5 p-3 border-b border-zinc-800">
        {QUICK_ACTIONS.map(action => (
          <button
            key={action.label}
            onClick={() =>
              handleQuickAction(
                action.label === 'Translate' ? 'TRANSLATE_PROMPT' : action.instruction,
              )
            }
            disabled={status === 'loading' || status === 'reindexing'}
            className="px-2.5 py-1 text-xs rounded border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {action.label}
          </button>
        ))}
        <button
          onClick={() => setShowTranslatePrompt(true)}
          disabled={status === 'loading' || status === 'reindexing'}
          className="px-2.5 py-1 text-xs rounded border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Translate
        </button>
      </div>

      {/* Translate sub-prompt */}
      {showTranslatePrompt && (
        <div className="flex gap-2 px-3 py-2 border-b border-zinc-800">
          <input
            value={translateLang}
            onChange={e => setTranslateLang(e.target.value)}
            placeholder="Language (e.g. Spanish)"
            className="flex-1 bg-zinc-800 text-zinc-200 text-sm rounded px-2 py-1 border border-zinc-700 outline-none focus:border-blue-500"
            onKeyDown={e => e.key === 'Enter' && handleTranslateSubmit()}
          />
          <button
            onClick={handleTranslateSubmit}
            className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-500"
          >
            Go
          </button>
          <button
            onClick={() => setShowTranslatePrompt(false)}
            className="px-2 py-1 text-xs rounded bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
          >
            ✕
          </button>
        </div>
      )}

      {/* Chat history */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {chatHistory.length === 0 && (
          <p className="text-zinc-500 text-sm text-center mt-8">
            Type an instruction or use a quick action above.
          </p>
        )}
        {chatHistory.map((msg, idx) => (
          <div
            key={idx}
            className={`text-sm rounded px-3 py-2 max-w-[90%] ${
              msg.role === 'user'
                ? 'ml-auto bg-blue-600/20 text-blue-200 border border-blue-700/30'
                : 'bg-zinc-800 text-zinc-300 border border-zinc-700'
            }`}
          >
            {msg.text}
          </div>
        ))}
        {status === 'loading' && (
          <div className="text-zinc-500 text-sm animate-pulse">Thinking...</div>
        )}
        {status === 'reindexing' && (
          <div className="text-amber-400 text-sm animate-pulse">Re-indexing document...</div>
        )}
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 p-3 border-t border-zinc-800">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Type an instruction..."
          disabled={status === 'loading' || status === 'reindexing' || status === 'diff-ready'}
          className="flex-1 bg-zinc-800 text-zinc-200 text-sm rounded px-3 py-2 border border-zinc-700 outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || status !== 'idle'}
          className="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `EditorPage.tsx`**

```tsx
// frontend/src/features/editor/EditorPage.tsx
import { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useEditor } from './useEditor';
import { DocumentViewer } from './DocumentViewer';
import { EditPanel } from './EditPanel';

export function EditorPage() {
  const { id } = useParams<{ id: string }>();
  const documentId = id ?? '';

  const { state, loadSections, sendInstruction, acceptDiff, rejectDiff } = useEditor(documentId);

  useEffect(() => {
    loadSections();
  }, [loadSections]);

  const activeSectionId = state.pendingDiff?.sectionId ?? null;

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800 shrink-0">
        <Link to="/documents" className="text-zinc-400 hover:text-zinc-200 transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <span className="text-sm font-medium text-zinc-200 truncate">
          {state.filename || 'Document Editor'}
        </span>
        {state.status === 'reindexing' && (
          <span className="ml-auto text-xs text-amber-400 animate-pulse">Re-indexing...</span>
        )}
        {state.status === 'loading' && (
          <span className="ml-auto text-xs text-blue-400 animate-pulse">Processing...</span>
        )}
      </header>

      {/* Two-panel body */}
      <div className="flex flex-1 min-h-0">
        {/* Left: Document viewer */}
        <div className="flex-1 border-r border-zinc-800 min-h-0">
          <DocumentViewer
            sections={state.sections}
            activeSectionId={activeSectionId}
            pendingDiff={
              state.pendingDiff
                ? { sectionId: state.pendingDiff.sectionId, diff: state.pendingDiff.diff }
                : null
            }
            onAccept={acceptDiff}
            onReject={rejectDiff}
          />
        </div>

        {/* Right: Edit panel */}
        <div className="w-80 shrink-0 min-h-0">
          <EditPanel
            chatHistory={state.chatHistory}
            status={state.status}
            onSend={sendInstruction}
            error={state.error}
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add route to `App.tsx`**

Add import:
```tsx
import { EditorPage } from "@/features/editor/EditorPage";
```

Add route inside `<Route element={<RequireAuth />}>` but **outside** `<Route element={<AppShell />}>` (the editor is full-screen, no sidebar):

```tsx
        {/* Protected — full screen, no AppShell */}
        <Route path="/documents/:id/edit" element={<EditorPage />} />

        {/* Protected — inside AppShell with sidebar */}
        <Route element={<AppShell />}>
```

Full updated `App.tsx`:
```tsx
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { AppShell } from "@/components/AppShell";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { ChatPage } from "@/features/chat/ChatPage";
import { EditorPage } from "@/features/editor/EditorPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<RequireAuth />}>
          {/* Full-screen editor — no AppShell sidebar */}
          <Route path="/documents/:id/edit" element={<EditorPage />} />

          {/* Standard app shell with sidebar */}
          <Route element={<AppShell />}>
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/documents" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Add Edit button to `DocumentsPage.tsx`**

Find the document card render section in `DocumentsPage.tsx`. Add an Edit button next to the existing "Purge Shard" (delete) button. Import `Link` from `react-router-dom` (already imported) and `Pencil` from `lucide-react`:

Add `Pencil` to the existing lucide-react import line:
```tsx
import { LayoutDashboard, Upload, Database, FileText, Activity, ShieldCheck, Zap, Plus, Pencil } from "lucide-react";
```

Find the delete button inside the document card and add the Edit button before it. Look for the pattern that renders each document card — add this button alongside the delete button (the exact surrounding JSX will depend on the card structure, but add it in the card actions area):

```tsx
<Link
  to={`/documents/${doc.id}/edit`}
  onClick={e => e.stopPropagation()}
  className="p-1.5 rounded text-zinc-400 hover:text-blue-400 hover:bg-blue-400/10 transition-colors"
  title="Edit document"
>
  <Pencil size={14} />
</Link>
```

Only render this button when `doc.status === 'ready'`.

- [ ] **Step 5: Start dev server and verify**

```bash
cd frontend && npm run dev
```

1. Navigate to `/documents`
2. Upload a `.txt` file and wait for status to show "Neural Link Active"
3. Click the pencil icon — should navigate to `/documents/{id}/edit`
4. Verify left panel shows document sections
5. Type "make this more concise" in the right panel and press Send
6. Verify diff appears in left panel with green/red highlights
7. Click Accept — verify "Re-indexing..." appears in header
8. Open a chat session with this document — verify the updated content appears in RAG answers

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/editor/ frontend/src/App.tsx frontend/src/features/documents/DocumentsPage.tsx
git commit -m "feat: add EditorPage, EditPanel, route, and Edit button — AI document editor complete"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by task |
|-----------------|-----------------|
| GET /sections endpoint | Task 7 |
| POST /edit endpoint | Task 7 |
| PUT /sections/{id} endpoint | Task 7 |
| DocumentSection dataclass | Task 3 |
| Shadow JSON for binary files | Task 3 |
| section_id on chunks | Task 1, 2 |
| Paragraph-level diff | Task 4 |
| LLM editing pipeline | Task 5 |
| Quick-action buttons | Task 8 (QUICK_ACTIONS), Task 12 (EditPanel) |
| Delete quick action | Task 5 (sentinel), Task 8 |
| Translate quick action | Task 12 (EditPanel language prompt) |
| Reindex Celery task | Task 6 |
| Surgical chunk deletion | Task 6 |
| Two-panel editor layout | Task 12 (EditorPage) |
| Document viewer left panel | Task 11 |
| Chat + quick actions right panel | Task 12 (EditPanel) |
| Accept/reject diff UI | Task 10 (DiffOverlay) |
| Edit button on documents page | Task 12 |
| Route /documents/:id/edit | Task 12 |
| Auto section detection via vector search | Task 5 (_identify_section) |
| Section not found fallback to section-0 | Task 5 (_identify_section) |
| 409 on locked document | Task 5, Task 7 |
| Re-indexing status indicator | Task 12 (EditorPage header) |
| Concurrent edit lock | Task 5 (status check in accept_edit) |

All spec requirements are covered.
