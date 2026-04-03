"""Unit tests for document parsers."""

import csv
import textwrap
from pathlib import Path

import pytest

from app.documents.parser import ParsedPage, _parse_csv, _parse_markdown, _parse_text


def test_parse_text_basic(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("Hello world.\nSecond line.")
    pages = _parse_text(f)
    assert len(pages) == 1
    assert "Hello world." in pages[0].text


def test_parse_text_empty(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_text("")
    pages = _parse_text(f)
    assert pages == []


def test_parse_markdown_sections(tmp_path: Path) -> None:
    content = textwrap.dedent("""
    # Introduction
    This is the intro.

    # Methods
    These are the methods.
    """)
    f = tmp_path / "doc.md"
    f.write_text(content.strip())
    pages = _parse_markdown(f)
    headings = [p.section_heading for p in pages]
    assert "Introduction" in headings
    assert "Methods" in headings


def test_parse_markdown_no_headings(tmp_path: Path) -> None:
    f = tmp_path / "plain.md"
    f.write_text("Just plain text without headings.")
    pages = _parse_markdown(f)
    assert len(pages) == 1
    assert "plain text" in pages[0].text


def test_parse_csv_basic(tmp_path: Path) -> None:
    f = tmp_path / "data.csv"
    with f.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name", "age", "city"])
        writer.writerow(["Alice", "30", "NYC"])
        writer.writerow(["Bob", "25", "LA"])
    pages = _parse_csv(f)
    assert len(pages) >= 1
    combined = " ".join(p.text for p in pages)
    assert "Alice" in combined
    assert "Bob" in combined


def test_parse_csv_empty(tmp_path: Path) -> None:
    f = tmp_path / "empty.csv"
    f.write_text("")
    pages = _parse_csv(f)
    assert pages == []
