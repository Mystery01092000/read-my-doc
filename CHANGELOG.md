# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-04-09

### Added
- Full-stack document Q&A application (FastAPI + React + PostgreSQL + pgvector)
- Hybrid retrieval: BM25 (tsvector) + vector search (pgvector) with Reciprocal Rank Fusion
- Cross-encoder reranking with `ms-marco-MiniLM-L-6-v2`
- Citation enforcement — every answer includes verified inline citations
- JWT authentication (register, login, refresh token rotation)
- Celery-based async document processing pipeline
- Multi-format document support: PDF, TXT, Markdown, CSV, Excel, PowerPoint
- SSE streaming for real-time chat responses
- Session history with sidebar navigation
- CI-gated RAG evaluation (faithfulness ≥ 0.8, citation accuracy ≥ 0.9)
- Groq LLM provider support (free tier alternative to Ollama)
- Self-hosted deployment via Docker Compose
- Free-tier cloud deployment guide (Vercel + Render + Supabase + Upstash + Groq)
