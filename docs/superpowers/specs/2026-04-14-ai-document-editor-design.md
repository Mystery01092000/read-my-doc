# AI Document Editor — Design Spec

**Date:** 2026-04-14
**Status:** Approved
**Scope:** Add an AI-powered document editing page where users can modify document content via natural language commands, review paragraph-level diffs, accept/reject changes, and have the RAG index automatically updated.

---

## 1. Overview

The current RAG system is read-only — documents can be uploaded and queried but never modified. This feature adds a two-panel editor page (`/documents/{id}/edit`) where:

- The **left panel** renders the document as navigable sections/paragraphs
- The **right panel** provides a chat interface with quick-action buttons for editing commands
- The AI proposes targeted edits to the most relevant section
- A paragraph-level diff is shown inline in the left panel
- Accepted changes are written back to disk and the RAG index is surgically updated

The UX is modeled after Claude's artifact editor: the document is always visible, edits are proposed before being applied, and the user has explicit accept/reject control.

---

## 2. Architecture

```
Frontend Editor Page (/documents/{id}/edit)
├── Left panel:  Document Viewer (sections, paragraph diff overlay)
└── Right panel: Edit Panel (chat history, quick-action buttons, text input)
         │
         ▼
Backend: DocumentEditorService
├── GET  /documents/{id}/sections          → parse file → return sections
├── POST /documents/{id}/edit              → instruction → LLM → diff
└── PUT  /documents/{id}/sections/{sid}   → accept diff → patch file + re-index
         │
         ▼
Existing infrastructure (reused without modification)
├── parser.py       → section extraction
├── chunker.py      → re-chunk edited section
├── embedder.py     → re-embed new chunks
├── chunks table    → delete old chunks, insert new ones
└── Celery worker   → background re-indexing task
```

**Key invariants:**
- The editor never modifies production code paths — it is additive only
- Re-indexing is always async (Celery task); the editor UI shows a status indicator
- A document locked in `processing` status is shown as read-only in the editor

---

## 3. Data Model

### 3.1 `DocumentSection` (ephemeral, not stored in DB)

Generated on-demand by parsing the file from disk. Not persisted.

```python
@dataclass
class DocumentSection:
    section_id: str           # e.g. "section-0", "page-3-heading-2"
    heading: str | None       # detected section title, if any
    content: str              # full text of this section
    paragraph_blocks: list[str]  # content split on \n\n boundaries
    page_number: int | None   # for PDF/PPTX
    char_start: int           # byte offset in full document text
    char_end: int             # byte offset end (for splice on accept)
```

### 3.2 Shadow Copy (for binary formats)

PDF, XLSX, and PPTX are binary formats that cannot be edited as text in place. On the first accepted edit, the system creates a plain-text shadow copy:

```
/data/uploads/{user_id}/{document_id}.shadow.txt
```

The shadow copy becomes the source of truth for all subsequent edits and RAG indexing. The original binary file is preserved untouched so users can always re-download it. A `has_shadow_copy: bool` flag is stored in the `documents` table.

### 3.3 Database Changes

New column on the `documents` table:

```sql
ALTER TABLE documents ADD COLUMN has_shadow_copy BOOLEAN NOT NULL DEFAULT FALSE;
```

New columns on the `chunks` table (populated during initial ingestion and re-indexing):

```sql
ALTER TABLE chunks ADD COLUMN char_start INTEGER;
ALTER TABLE chunks ADD COLUMN char_end   INTEGER;
```

`char_start`/`char_end` are byte offsets into the full document text (or shadow copy text). They are required for surgical re-indexing — the editor uses them to identify which chunks overlap with an edited section and must be deleted/replaced. The `chunker.py` must be updated to track and store these offsets during initial ingestion.

---

## 4. API Endpoints

### 4.1 `GET /documents/{id}/sections`

Returns the document parsed into sections.

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "report.pdf",
  "file_type": "pdf",
  "has_shadow_copy": false,
  "sections": [
    {
      "section_id": "section-0",
      "heading": "Introduction",
      "content": "Lorem ipsum...",
      "paragraph_blocks": ["Lorem ipsum...", "Dolor sit amet..."],
      "page_number": 1,
      "char_start": 0,
      "char_end": 412
    }
  ]
}
```

**Error cases:**
- `404` — document not found or not owned by user
- `409` — document status is `pending` or `processing` (not ready for editing)

### 4.2 `POST /documents/{id}/edit`

Sends an editing instruction. Returns a proposed diff — nothing is written yet.

**Request:**
```json
{
  "instruction": "make the introduction more concise",
  "section_id": null
}
```

`section_id` is optional. If `null`, the backend auto-detects the most relevant section via vector search on the instruction.

**Response:**
```json
{
  "section_id": "section-0",
  "heading": "Introduction",
  "original_paragraphs": ["Lorem ipsum...", "Dolor sit amet..."],
  "edited_paragraphs": ["Concise version..."],
  "diff": [
    { "type": "removed",   "text": "Lorem ipsum..." },
    { "type": "removed",   "text": "Dolor sit amet..." },
    { "type": "added",     "text": "Concise version..." }
  ]
}
```

**Error cases:**
- `422` — instruction is empty
- `400` — LLM returned invalid/empty edit (too short, nonsensical length ratio)
- `409` — document is locked (re-indexing in progress)

### 4.3 `PUT /documents/{id}/sections/{section_id}`

Accepts a proposed edit. Patches the file and triggers re-indexing.

**Request:**
```json
{
  "edited_paragraphs": ["Concise version..."]
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "section_id": "section-0",
  "status": "reindexing",
  "task_id": "celery-task-uuid"
}
```

The document status transitions to `processing` during re-indexing, then back to `ready` on completion.

---

## 5. LLM Editing Pipeline

When `POST /documents/{id}/edit` is called:

```
1. SECTION IDENTIFICATION
   if section_id provided:
     load that section from parsed sections list
   else:
     embed instruction using existing embedder
     run vector search against document's chunks (filtered by document_id)
     find the section whose char range contains the top-ranked chunk

2. LLM EDIT
   system_prompt = """
     You are a document editor. You will receive a section of text and an
     editing instruction. Return ONLY the edited version of the section text
     with the instruction applied. Preserve all headings, formatting, and
     content not targeted by the instruction. Do not add commentary or
     explanations — return only the edited text.
   """

   user_message = f"INSTRUCTION: {instruction}\n\nSECTION:\n{section.content}"

   Call configured LLM provider (Ollama / OpenAI / Groq)
   Validate response: non-empty, length ratio between 0.1x and 5x of original

3. DIFF GENERATION (server-side, Python difflib)
   Split original and edited text on \n\n to get paragraph lists
   Run difflib.SequenceMatcher on paragraph lists
   Produce: list of {type: "unchanged" | "removed" | "added", text: str}

4. RETURN diff response (no file writes yet)
```

### 5.1 Quick-Action Instructions

Quick-action buttons on the frontend send pre-built instruction strings to the same `POST /documents/{id}/edit` endpoint:

| Button | Instruction string |
|--------|--------------------|
| Fix Grammar | `"Fix grammar and spelling errors only. Do not change meaning or structure."` |
| Summarize | `"Summarize this section to 30% of its current length, preserving key points."` |
| Expand | `"Expand this section with more detail and supporting explanation."` |
| Translate | `"Translate this section to {language}."` (frontend prompts for language first) |
| Delete | Skips LLM — returns diff that removes entire section content |

---

## 6. Re-indexing Strategy

When `PUT /documents/{id}/sections/{section_id}` is accepted:

```
1. PATCH FILE ON DISK
   TXT / MD:
     load file text
     splice: text[:char_start] + edited_content + text[char_end:]
     write back to same path

   PDF / XLSX / PPTX (binary):
     if not has_shadow_copy:
       run parser on original file → full text
       write to {document_id}.shadow.txt
       set has_shadow_copy = True in DB
     splice shadow copy as above

2. DELETE OLD CHUNKS
   SELECT id FROM chunks
     WHERE document_id = ? AND char_start < section.char_end
       AND char_end > section.char_start
   DELETE those chunk IDs

3. RE-CHUNK & RE-EMBED
   Run chunk_pages() on edited section text
   Run embedder.embed_chunks() on new chunks
   INSERT new chunks into chunks table
   Rebuild tsvector on new chunks

4. UPDATE DOCUMENT METADATA
   UPDATE documents SET
     tokens_embedded = (SELECT SUM(token_count) FROM chunks WHERE document_id = ?),
     updated_at = NOW()
   WHERE id = ?

5. SET STATUS BACK TO ready
```

Re-indexing runs as a Celery task. Document status is set to `processing` before the task starts and back to `ready` (or `failed`) when it completes.

---

## 7. Frontend

### 7.1 Route

`/documents/:id/edit` — new page, accessible via an "Edit" button added to each document card on the existing `DocumentsPage`.

### 7.2 Layout

```
┌─────────────────────────────┬──────────────────────────────┐
│  DOCUMENT VIEWER (left)     │  EDIT PANEL (right)          │
│                             │                              │
│  [← Back]  Filename.pdf     │  Quick actions:              │
│  ─────────────────────      │  [Fix Grammar] [Summarize]   │
│                             │  [Expand] [Translate][Delete]│
│  Introduction               │  ─────────────────────────  │
│  Lorem ipsum dolor sit...   │                              │
│  amet consectetur...        │  Chat history               │
│                             │  ┌─────────────────────┐    │
│  ■ Section 2 ◄ highlighted  │  │ You: make intro      │    │
│  [removed] Old paragraph    │  │      more concise    │    │
│  [added]   New paragraph    │  │                      │    │
│                             │  │ AI: Proposed edit ↙  │    │
│  [✓ Accept] [✗ Reject]      │  └─────────────────────┘    │
│                             │                              │
│  Section 3                  │  [Type an instruction...]    │
│  More content here...       │  [Send ↵]                    │
└─────────────────────────────┴──────────────────────────────┘
```

### 7.3 Frontend State

```typescript
type EditorState = {
  sections: DocumentSection[]
  pendingDiff: {
    section_id: string
    diff: DiffBlock[]
    edited_paragraphs: string[]
  } | null
  editingStatus: 'idle' | 'loading' | 'diff-ready' | 'reindexing'
  chatHistory: ChatMessage[]
  error: string | null
}
```

### 7.4 Interaction Flow

1. Page loads → `GET /documents/{id}/sections` → renders all sections in left panel
2. User types instruction or clicks quick-action → `POST /documents/{id}/edit`
3. Left panel scrolls to and highlights the affected section — shows paragraph diff inline (green = added, red strikethrough = removed)
4. Accept/Reject buttons appear anchored below the diff
5. **Accept** → `PUT /documents/{id}/sections/{section_id}` → left panel updates with new text, "Re-indexing..." status indicator appears in header
6. **Reject** → diff clears, section reverts to original display
7. Each edit is independent; a new instruction can be sent after accept or reject

### 7.5 New Files

```
frontend/src/features/editor/
├── EditorPage.tsx          # page shell, two-panel layout
├── DocumentViewer.tsx      # left panel, section list, diff overlay
├── SectionBlock.tsx        # individual section with accept/reject UI
├── DiffOverlay.tsx         # paragraph-level diff rendering
├── EditPanel.tsx           # right panel, chat + quick actions
└── useEditor.ts            # state management hook

frontend/src/api/editor.ts  # API client for 3 new endpoints
```

---

## 8. Backend New Modules

```
backend/app/documents/
├── section_extractor.py    # parse file → list[DocumentSection]
├── diff_generator.py       # difflib wrapper → list[DiffBlock]
└── editor_service.py       # orchestrates: section id → LLM → diff → re-index

backend/app/documents/router.py  # add 3 new routes
backend/tasks/document_tasks.py  # add reindex_section Celery task
```

`DocumentEditorService` depends on existing `embedder`, `retriever` (for auto section detection), and the configured LLM client — no new infrastructure.

---

## 9. Error Handling

| Scenario | Handling |
|----------|----------|
| Document status is pending/processing | `GET /sections` returns `409`; frontend shows "Document not ready for editing" |
| LLM returns empty or implausibly short/long edit | Return `400` with message; frontend shows error in chat |
| Section not found by vector search | Fall back to first section; notify user in chat: "Editing first section — specify a section if this is wrong" |
| Re-indexing fails | Mark document as `failed`, show error banner in editor, preserve original content |
| Binary file (PDF/XLSX/PPTX) first edit | Create shadow copy silently; show one-time notice: "Original file preserved — editing plain text version" |
| Concurrent edit while re-indexing | Document status = `processing`; editor shows read-only overlay until status returns to `ready` |

---

## 10. Testing

| Layer | Test |
|-------|------|
| Unit | `section_extractor.py` — correct sections from each file type (TXT, MD, PDF, CSV, XLSX, PPTX) |
| Unit | `diff_generator.py` — unchanged/removed/added blocks correct for known inputs |
| Unit | LLM prompt construction — system prompt present, section and instruction injected |
| Unit | Shadow copy creation — binary file produces correct plain-text output |
| Integration | `POST /edit` full round-trip with mocked LLM — correct diff returned |
| Integration | `PUT /sections/{id}` — file patched, old chunks deleted, new chunks inserted and embedded |
| Integration | Concurrent edit lock — second request while reindexing returns `409` |
| E2E | Upload TXT → open editor → send instruction → accept → query RAG → updated content returned in answer |

---

## 11. Out of Scope

- Document version history / undo beyond session
- Collaborative editing (multiple users on same document)
- Editing within a chat session (editor is a separate page only)
- Re-generating the original binary file (PDF/DOCX) from edits
- Streaming the LLM edit response (edit responses are short enough to await fully)
