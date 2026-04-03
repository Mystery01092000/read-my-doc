# Product Requirements Document (PRD)
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04  
**Status:** Approved

---

## 1. Overview

Ask My Docs is a full-stack RAG (Retrieval-Augmented Generation) application. Users log in, upload documents, and chat with them. The system uses hybrid retrieval (BM25 + vector search), cross-encoder reranking, and enforced citations to deliver accurate, auditable answers.

---

## 2. User Personas

**Alex** — a knowledge worker who needs to quickly find information across multiple internal PDFs.  
**Sam** — an analyst who queries Excel/CSV reports and needs cited, auditable outputs.

---

## 3. User Stories

### Authentication
- As a new user, I can register with my email and password
- As a returning user, I can log in and receive a session token
- As an authenticated user, my token refreshes automatically so I'm not logged out mid-session

### Documents
- As a user, I can upload a PDF, TXT, MD, CSV, Excel, or PPTX file (up to 50 MB)
- As a user, I can see my uploaded documents with their processing status (pending / processing / ready / failed)
- As a user, I can delete a document and all its associated chat data
- As a user, I receive a clear error message if my file fails to process

### Chat
- As a user, I can start a new chat session and select which of my documents to chat with
- As a user, I receive answers with inline citations: `[Doc: filename, Page 3]`
- As a user, I can click a citation to see the exact source text chunk
- As a user, the response streams word-by-word so I don't wait for the full answer
- As a user, I can continue typing while waiting for a response

### History
- As a user, I can see all my previous chat sessions in a sidebar
- As a user, I can click a session to reopen it and see the full conversation
- As a user, sessions are titled with an auto-generated summary of the first question

---

## 4. Functional Requirements

### 4.1 Auth API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Create account (email + password) |
| `/auth/login` | POST | Return access token + refresh token |
| `/auth/refresh` | POST | Exchange refresh token for new access token |
| `/auth/logout` | POST | Revoke refresh token |

### 4.2 Documents API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents` | GET | List user's documents (paginated) |
| `/documents` | POST | Upload document (multipart/form-data) |
| `/documents/{id}` | GET | Document detail + processing status |
| `/documents/{id}` | DELETE | Delete document + all chunks |

### 4.3 Chat API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/sessions` | GET | List user's sessions |
| `/chat/sessions` | POST | Create session (body: `{document_ids, title?}`) |
| `/chat/sessions/{id}` | GET | Session detail with messages |
| `/chat/sessions/{id}` | DELETE | Delete session |
| `/chat/sessions/{id}/messages` | POST | Send message → SSE stream of answer + citations |

---

## 5. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | First token latency < 3s; full response < 30s for typical queries |
| Scalability | Support 100 concurrent users on a 4-core / 16GB host |
| Security | JWT auth; bcrypt passwords; user data isolation enforced at DB query level |
| Reliability | Celery retry on transient failures; document status reflects permanent errors |
| Observability | Structured logs; Celery Flower dashboard for task monitoring |
| Portability | Runs entirely with `docker compose up` |

---

## 6. UI Requirements

### Pages
1. **Login / Register** — email + password form, redirect on success
2. **Documents** — file upload dropzone, document list with status chips, delete button
3. **Chat** — left sidebar (session list + new session button), main chat area (messages + citation chips), document picker modal for new sessions
4. **Session history** — accessible from sidebar; clicking a session loads it in the chat view

### Components
- `FileUpload` — drag-and-drop + click-to-browse, shows progress and status badge
- `ChatMessage` — renders markdown; inline `CitationChip` components that expand on click
- `CitationDrawer` — shows source chunk text, filename, page number on citation click
- `SessionSidebar` — scrollable list of sessions with title and date

---

## 7. Technical Architecture

See `IMPLEMENTATION.md` for the full technical design.

---

## 8. Out of Scope (v1)

- OCR for scanned/image PDFs
- Multi-tenancy / organization accounts
- Document sharing between users
- Real-time collaborative chat
- Mobile app
