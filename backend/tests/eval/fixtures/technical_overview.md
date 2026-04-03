# Technical Overview

## Hybrid Retrieval

The system uses hybrid retrieval to find the most relevant document chunks for a user query. This combines two complementary approaches:

1. **Vector similarity search** (dense retrieval): The user query is embedded using the same model as the document chunks (BAAI/bge-small-en-v1.5, 384 dimensions). Cosine similarity is computed using pgvector's HNSW index.

2. **BM25 keyword search** (sparse retrieval): PostgreSQL's built-in tsvector and ts_rank are used to score chunks based on keyword overlap between the query and chunk text.

The two result lists are merged using **Reciprocal Rank Fusion (RRF)**, which combines rankings without requiring score normalization. RRF is robust because it only uses rank positions, not raw scores.

## Cross-Encoder Reranking

After hybrid retrieval returns the top-20 candidates, a cross-encoder model (cross-encoder/ms-marco-MiniLM-L-6-v2) scores each (query, chunk) pair jointly. The top-5 scoring chunks are selected and passed to the LLM.

## Citation Enforcement

Every LLM response must include citations. The system enforces this through:
1. A system prompt that instructs the model to return structured JSON with inline citation markers
2. Post-processing that validates all cited chunk IDs against the retrieved chunk set
3. Any citation IDs not present in the retrieved chunks are stripped from the response

## CI Evaluation Pipeline

A CI-gated evaluation pipeline runs automatically on pull requests that modify the RAG pipeline. The pipeline:
- Loads a golden test dataset of question/answer pairs
- Runs the full RAG pipeline on each question
- Measures RAGAS metrics: faithfulness, answer relevance, context precision
- Measures citation accuracy: the percentage of returned citations that reference valid, retrieved chunks

**Thresholds for CI to pass:**
- Faithfulness: must be >= 0.8 (80%)
- Citation accuracy: must be >= 0.9 (90%)

If either threshold is not met, the pull request is blocked from merging.
