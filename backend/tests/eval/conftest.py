"""Shared fixtures for the RAG evaluation suite."""

import json
from pathlib import Path
from typing import TypedDict

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class GoldenItem(TypedDict):
    id: str
    question: str
    ground_truth: str
    source_doc: str
    expected_has_citation: bool


@pytest.fixture(scope="session")
def golden_dataset() -> list[GoldenItem]:
    path = FIXTURES_DIR / "golden.jsonl"
    items: list[GoldenItem] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


@pytest.fixture(scope="session")
def fixture_docs() -> dict[str, str]:
    """Return {filename: content} for all fixture documents."""
    docs: dict[str, str] = {}
    for fpath in FIXTURES_DIR.iterdir():
        if fpath.suffix in {".txt", ".md", ".csv"}:
            docs[fpath.name] = fpath.read_text()
    return docs
