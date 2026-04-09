# Document Update Pipeline + Base64 Converter

## Context

Two new features for the read-my-doc platform:

1. **Document Update Pipeline** — Users describe edits in natural language (e.g. "change the title on slide 3"). The LLM interprets the instruction into structured edit operations, applies them to the actual file (PDF/PPTX/XLSX/CSV/TXT/MD), then re-indexes the document so the RAG search stays in sync.

2. **Base64 Document Converter** — A new standalone product on the platform. Accepts a base64 string → detects file type via magic bytes → decodes to the correct file. Or the reverse: upload a file → get base64 string back. Runs asynchronously via Celery to manage server load.

---

## Phase 0: Shared Refactoring (prerequisite)

Extract reusable logic before building either feature.

### 0a. Extract reindex logic into `backend/app/documents/indexer.py`

Currently, the parse → chunk → embed → store pipeline lives inline in `backend/tasks/document_tasks.py:48-101`. Extract it into a reusable function:

```python
# backend/app/documents/indexer.py
async def reindex_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Delete existing chunks, re-parse, re-chunk, re-embed, store new chunks, update tsvectors."""
```

Then `_process_document_async` in `document_tasks.py` calls `reindex_document()` instead of inlining the pipeline. The document update task will also call this same function.

### 0b. Extract LLM client into `backend/app/llm/client.py`

Move `_call_llm`, `_call_ollama`, `_call_openai` (and their streaming variants) from `backend/app/rag/generator.py` into a shared module. Both RAG and document editing need to call the LLM. `generator.py` will import from `llm/client.py`.

### 0c. Migration `0006_add_document_versioning.py`

Add to `documents` table:
- `version INTEGER NOT NULL DEFAULT 1`
- `updated_at TIMESTAMP WITH TZ nullable`

---

## Phase 1: Base64 Converter (no LLM dependency — simpler, build first)

### 1a. New dependency

Add `filetype>=1.2.0` to `backend/pyproject.toml` — detects file type from magic bytes (images, PDFs, Office docs). Falls back to `mimetypes.guess_type()` with filename hint.

### 1b. Migration `0007_add_conversions.py`

New table **`conversions`**:

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK → users | indexed |
| direction | VARCHAR(10) | `"encode"` or `"decode"` |
| input_filename | VARCHAR(512) nullable | original filename (for encode) |
| input_size_bytes | BIGINT | |
| output_filename | VARCHAR(512) nullable | detected/generated name |
| detected_mime | VARCHAR(128) nullable | MIME from magic bytes |
| output_path | VARCHAR(1024) nullable | path on disk |
| status | VARCHAR(20) | `pending → processing → ready → failed` |
| error_message | TEXT nullable | |
| created_at | TIMESTAMP WITH TZ | |
| expires_at | TIMESTAMP WITH TZ nullable | auto-cleanup deadline |

Storage: `/data/conversions/{user_id}/{conversion_id}{ext}`

### 1c. New backend module `backend/app/converter/`

| File | Purpose |
|------|---------|
| `models.py` | `Conversion` SQLAlchemy model |
| `repository.py` | `ConversionRepository` — CRUD + status updates |
| `schemas.py` | `Base64DecodeRequest`, `ConversionResponse`, etc. |
| `detector.py` | `detect_mime(data: bytes) -> tuple[str, str]` — returns (mime, extension) using `filetype` + `mimetypes` fallback |
| `service.py` | `ConverterService` — validates input, saves to disk, dispatches Celery task |
| `router.py` | API endpoints (see below) |

### 1d. API endpoints

| Method | Path | Body/Params | Description |
|--------|------|-------------|-------------|
| POST | `/converter/decode` | `{ data: str, filename?: str }` | Submit base64 → decode to file (202) |
| POST | `/converter/encode` | multipart file upload | Upload file → encode to base64 (202) |
| GET | `/converter/{id}` | | Poll conversion status + result |
| GET | `/converter/{id}/download` | | Download decoded file (for decode direction) |
| GET | `/converter/{id}/base64` | | Get base64 string (for encode direction) |
| GET | `/converter` | `?page=&limit=` | List user's conversions (paginated) |

### 1e. Celery tasks — `backend/tasks/converter_tasks.py`

Two tasks, following the existing pattern (bind=True, max_retries=2, asyncio.run bridge, own DB session):

**`decode_base64(conversion_id: str)`**:
1. Read base64 input from disk (saved as `.b64.txt` by the service)
2. Decode to bytes
3. Detect MIME type via `detector.detect_mime()`
4. Write decoded bytes to output_path with correct extension
5. Update conversion record with `detected_mime`, `output_filename`, `output_path`, status=`ready`

**`encode_file(conversion_id: str)`**:
1. Read file from input_path
2. Base64-encode (stream in chunks for memory efficiency)
3. Write base64 string to `{output_path}.b64.txt`
4. Set status=`ready`

Rate limiting: `rate_limit="10/m"` on both tasks + per-user concurrency check in service layer.

Add `"tasks.converter_tasks"` to `backend/tasks/worker.py` include list.

### 1f. Config additions — `backend/app/config.py`

- `conversion_dir: str = "/data/conversions"`
- `max_base64_size_mb: int = 25`
- `conversion_expiry_hours: int = 24`

### 1g. Register router — `backend/app/main.py`

Add `converter` router at prefix `/converter`.

### 1h. Frontend

New files:

| File | Purpose |
|------|---------|
| `frontend/src/features/converter/ConverterPage.tsx` | Main page with Encode / Decode tabs |
| `frontend/src/features/converter/EncodeSection.tsx` | File dropzone → shows base64 output with copy button |
| `frontend/src/features/converter/DecodeSection.tsx` | Textarea for base64 → shows detected type + download button |
| `frontend/src/features/converter/ConversionHistoryList.tsx` | List of past conversions with status |
| `frontend/src/api/converter.ts` | API client functions |

Type additions in `frontend/src/types/index.ts`:
```typescript
interface Conversion {
  id: string;
  direction: "encode" | "decode";
  inputFilename: string | null;
  inputSizeBytes: number;
  outputFilename: string | null;
  detectedMime: string | null;
  status: "pending" | "processing" | "ready" | "failed";
  createdAt: string;
}
```

Routing: Add `/converter` route in `App.tsx` inside `AppShell`. Add nav link in sidebar.

---

## Phase 2: Document Update Pipeline

### 2a. Migration `0008_add_document_updates.py`

New table **`document_updates`**:

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| document_id | UUID FK → documents (CASCADE) | indexed |
| user_id | UUID FK → users (CASCADE) | indexed |
| instruction | TEXT | user's natural-language edit request |
| edit_operations | JSONB nullable | LLM-generated structured ops (stored for auditability) |
| status | VARCHAR(20) | `pending → processing → applying → reindexing → ready → failed` |
| error_message | TEXT nullable | |
| version | INTEGER | document version after this update |
| created_at | TIMESTAMP WITH TZ | |

### 2b. Structured edit schemas — `backend/app/documents/edit_schemas.py`

Frozen dataclasses per file type that the LLM will produce:

```python
@dataclass(frozen=True)
class TextEdit:          # TXT, MD, CSV
    action: Literal["replace", "insert_line", "delete_line", "append"]
    search_text: str | None
    new_text: str | None
    line_number: int | None

@dataclass(frozen=True)
class PdfEdit:           # PDF (PyMuPDF)
    page_number: int
    action: Literal["replace_text", "insert_text", "delete_text"]
    search_text: str | None
    new_text: str | None

@dataclass(frozen=True)
class PptxEdit:          # PPTX
    slide_number: int
    action: Literal["replace_text", "set_title", "add_text"]
    search_text: str | None
    new_text: str

@dataclass(frozen=True)
class SpreadsheetEdit:   # XLSX
    sheet_name: str | None
    row: int
    column: str | int
    new_value: str
```

### 2c. Document editor — `backend/app/documents/editor.py`

Mirrors `parser.py` with a dispatch pattern. Per-type writer functions:

- `_edit_pdf(path, edits: list[PdfEdit])` — PyMuPDF `page.search_for()` + `page.add_redact_annot()` + `page.apply_redactions()` + insert
- `_edit_pptx(path, edits: list[PptxEdit])` — python-pptx slide/shape text replacement
- `_edit_excel(path, edits: list[SpreadsheetEdit])` — openpyxl cell writes
- `_edit_text(path, edits: list[TextEdit])` — plain string/line manipulation for TXT/MD/CSV

Each function backs up the original to `{path}.v{old_version}` before writing.

### 2d. Edit prompt template — `backend/app/documents/edit_prompts.py`

LLM prompt that takes: document type, document text summary, user instruction, and the JSON schema of valid edit operations. Returns structured JSON array of edit operations.

### 2e. Backend wiring

Modify existing files:

- `backend/app/documents/models.py` — Add `DocumentUpdate` model
- `backend/app/documents/repository.py` — Add `DocumentUpdateRepository` (CRUD + status), add `ChunkRepository.delete_by_document()` for reindex
- `backend/app/documents/router.py` — Add update endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents/{id}/updates` | Submit update instruction (202) |
| GET | `/documents/{id}/updates` | List update history |
| GET | `/documents/{id}/updates/{update_id}` | Get update status |
| GET | `/documents/{id}/download` | Download current file |

New files:
- `backend/app/documents/update_schemas.py` — `DocumentUpdateRequest`, `DocumentUpdateResponse`
- `backend/app/documents/update_service.py` — validates document ownership, rejects concurrent edits (check for in-flight updates), dispatches task

### 2f. Celery task — `backend/tasks/document_update_tasks.py`

**`update_document(update_id: str)`** flow:
1. Fetch `DocumentUpdate` + parent `Document`
2. Status → `processing`
3. Parse current document text (reuse `parse_file()`)
4. Call LLM via `llm/client.py` with edit prompt → get structured edit operations JSON
5. Store `edit_operations` on the update record
6. Status → `applying`
7. Call `editor.apply_edits(path, file_type, operations)` — backs up original, writes modified file
8. Status → `reindexing`
9. Call `reindex_document(session, document_id)` from `indexer.py`
10. Bump `Document.version`, set `Document.updated_at`
11. Status → `ready`

Concurrency safety: check `Document.version` matches expected before applying. Reject if another update is in-flight (status in `pending/processing/applying/reindexing`).

Add `"tasks.document_update_tasks"` to `worker.py` include list.

### 2g. Frontend

New files:

| File | Purpose |
|------|---------|
| `frontend/src/features/documents/DocumentUpdateModal.tsx` | Modal: textarea for instruction, progress display through statuses |
| `frontend/src/features/documents/UpdateHistoryPanel.tsx` | List past updates with status badges |

Modify:
- `frontend/src/features/documents/DocumentsPage.tsx` — Add "Edit" button per document card
- `frontend/src/api/documents.ts` — Add `submitUpdate()`, `getUpdates()`, `downloadDocument()`
- `frontend/src/types/index.ts` — Add `DocumentUpdate` interface

---

## Key Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM misinterprets edit instruction | HIGH | Store backup at `{path}.v{N}` before every edit; store `edit_operations` JSON for auditability; consider a preview/confirm step as future enhancement |
| PDF text replacement overflow | MEDIUM | PyMuPDF can't reflow — limit to simple replacements; document this limitation in the LLM prompt |
| Large base64 strings cause OOM | MEDIUM | Cap at 25 MB input; stream encode/decode via chunked read/write |
| Concurrent document edits race | MEDIUM | Optimistic locking on `Document.version`; reject while another update is in-flight |
| MIME detection failure | LOW | `filetype` lib → `mimetypes.guess_type()` fallback → default to `application/octet-stream` + `.bin` |

---

## Verification

1. **Base64 Converter**: Upload a PNG via `/converter/encode` → poll → get base64 → submit to `/converter/decode` → download → compare files
2. **Document Update**: Upload a PPTX → status=ready → POST `/documents/{id}/updates` with `"Change the title on slide 1 to Hello World"` → poll through statuses → download updated file → verify title changed → ask a chat question to verify reindex worked
3. **Rate limiting**: Submit 15 rapid decode requests → verify only 10/min are processed, rest queued
4. **Error handling**: Submit invalid base64 → verify status=failed with clear error message
5. **Backup**: After document update, verify `{path}.v1` backup file exists on disk
