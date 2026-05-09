from __future__ import annotations

import json
from pathlib import Path

import fitz

from active_recall_pipeline.config import PipelineConfig


def run(cfg: PipelineConfig) -> None:
    """
    PARSE — Extract text from PDFs and split into sections.

    Input: config.interim_dir/ingest_metadata.json
    Output: config.interim_dir/parsed_sections.json

    For each PDF:
    - If full_book mode: detect chapter boundaries using TOC
    - If chapter mode: treat entire PDF as one chapter
    - Split chapters into sections of roughly 3000 words at paragraph boundaries

    Model: PyMuPDF (code only)
    """
    metadata_file = cfg.interim_dir / "ingest_metadata.json"
    with open(metadata_file) as f:
        metadata_list = json.load(f)

    sections = []
    section_counter = 1

    for entry in metadata_list:
        pdf_path = Path(entry["pdf_path"])
        doc = fitz.open(pdf_path)

        if entry["input_mode"] == "full_book":
            chapters = _extract_chapters_from_toc(doc, entry)
        else:
            chapters = _extract_single_chapter(doc, entry)

        for chapter in chapters:
            chapter_sections = _split_chapter_into_sections(chapter, section_counter)
            sections.extend(chapter_sections)
            section_counter += len(chapter_sections)

        doc.close()

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "parsed_sections.json"
    with open(output_file, "w") as f:
        json.dump(sections, f, indent=2)


def _extract_chapters_from_toc(doc, entry: dict) -> list[dict]:
    """Extract chapters using table of contents."""
    toc = doc.get_toc()
    if not toc:
        text = _extract_pdf_text(doc, 0, doc.page_count - 1)
        return [{
            "pdf_path": entry["pdf_path"],
            "chapter_num": 1,
            "chapter_title": entry.get("chapter_title", ""),
            "text": text,
        }]

    chapters = []
    level_1_toc = [(i, item) for i, item in enumerate(toc) if item[0] == 1]
    for list_idx, (i, toc_item) in enumerate(level_1_toc):
        page_num = toc_item[2]
        title = toc_item[1]

        next_entry = level_1_toc[list_idx + 1] if list_idx + 1 < len(level_1_toc) else None
        next_page = next_entry[1][2] if next_entry else doc.page_count

        text = _extract_pdf_text(doc, page_num - 1, next_page - 1)

        chapters.append({
            "pdf_path": entry["pdf_path"],
            "chapter_num": list_idx + 1,
            "chapter_title": title,
            "text": text,
        })

    return chapters


def _extract_single_chapter(doc, entry: dict) -> list[dict]:
    """Extract entire PDF as single chapter."""
    text = _extract_pdf_text(doc, 0, doc.page_count - 1)
    return [{
        "pdf_path": entry["pdf_path"],
        "chapter_num": entry["chapter_num"],
        "chapter_title": entry.get("chapter_title", ""),
        "text": text,
    }]


def _extract_pdf_text(doc, start_page: int, end_page: int) -> str:
    """Extract text from PDF pages."""
    end_page = min(end_page, doc.page_count - 1)
    text = ""
    for page_num in range(start_page, end_page + 1):
        page = doc[page_num]
        text += page.get_text()
    return text


def _split_chapter_into_sections(chapter: dict, start_section_id: int) -> list[dict]:
    """Split chapter into sections of roughly 3000 words at paragraph boundaries."""
    text = chapter["text"]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    sections = []
    current_section = ""
    section_id = start_section_id

    for para in paragraphs:
        test_section = current_section + para + "\n\n" if current_section else para + "\n\n"
        word_count = len(test_section.split())

        if word_count >= 3000 and current_section:
            sections.append({
                "pdf_path": chapter["pdf_path"],
                "chapter_num": chapter["chapter_num"],
                "chapter_title": chapter["chapter_title"],
                "section_id": section_id,
                "text": current_section.strip(),
            })
            current_section = para + "\n\n"
            section_id += 1
        else:
            current_section = test_section

    if current_section.strip():
        sections.append({
            "pdf_path": chapter["pdf_path"],
            "chapter_num": chapter["chapter_num"],
            "chapter_title": chapter["chapter_title"],
            "section_id": section_id,
            "text": current_section.strip(),
        })

    return sections
