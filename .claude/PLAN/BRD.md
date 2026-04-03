# Business Requirements Document (BRD)
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04  
**Status:** Approved

---

## 1. Executive Summary

Ask My Docs is a domain-specific document Q&A platform that enables users to upload proprietary documents and query them using natural language. It addresses the need for accurate, cited answers from unstructured documents without leaking data to third-party training pipelines.

---

## 2. Business Objectives

| # | Objective |
|---|-----------|
| 1 | Enable users to upload and query their own documents via natural language |
| 2 | Ensure every AI-generated answer cites its source (page/section) for auditability |
| 3 | Preserve session history so users can revisit prior conversations |
| 4 | Provide a quality gate (CI-gated eval) to prevent RAG quality regression |
| 5 | Run entirely self-hosted to satisfy data-residency requirements |

---

## 3. Stakeholders

- **End users** — knowledge workers who need to query internal documents
- **Developers** — engineers who maintain and extend the platform
- **Operators** — teams deploying the system on-premise or in private cloud

---

## 4. Business Requirements

### 4.1 Authentication & Access Control
- BR-01: Users must register with email and password
- BR-02: Users must authenticate before accessing any feature
- BR-03: Each user's documents and sessions are isolated from other users

### 4.2 Document Management
- BR-04: Users can upload documents in PDF, TXT, Markdown, CSV, Excel, and PowerPoint formats
- BR-05: Maximum file size per upload: 50 MB
- BR-06: Users can view a list of their uploaded documents with processing status
- BR-07: Users can delete documents (and all associated data)

### 4.3 Chat & Q&A
- BR-08: Users can start a new chat session against one or more of their documents
- BR-09: Every AI response must include inline citations referencing specific document chunks (page number, section heading, and text snippet)
- BR-10: Citations must be verifiable — the system must not hallucinate source references
- BR-11: Chat responses must stream progressively (no waiting for full response)

### 4.4 History
- BR-12: Users can view a list of all previous chat sessions
- BR-13: Users can re-open and continue any previous session
- BR-14: Session titles are auto-generated from the first question

### 4.5 Quality & Reliability
- BR-15: The RAG pipeline must maintain faithfulness ≥ 0.8 (RAGAS) and citation accuracy ≥ 0.9 as measured by the CI eval pipeline
- BR-16: Document processing must be asynchronous — the UI must show real-time status updates

---

## 5. Constraints

- Must run fully on-premise with Docker Compose
- No reliance on external AI APIs by default (OpenAI configurable as fallback)
- Must not transmit user documents to third-party services

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| RAGAS Faithfulness | ≥ 0.80 |
| Citation Accuracy | ≥ 0.90 |
| Document processing time (typical PDF) | < 60 seconds |
| Query response time (first token) | < 3 seconds |
| Test coverage | ≥ 80% |
