from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig, Exam, UPPSC_SUBJECTS


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    INGEST — Read PDF filenames, extract metadata.

    Input: PDF files in cfg.raw_dir
    Supports two modes detected automatically:
      Mode 1 — Full book: Subject_BookName.pdf directly in raw_dir
      Mode 2 — Chapter folder: Subject_BookName/Ch01_Title.pdf in subfolder

    Output: Metadata JSON in cfg.interim_dir/ingest_metadata.json
      [{"exam": "...", "book": "...", "subject": "...", "chapter_num": ...,
        "chapter_title": "...", "input_mode": "...", "pdf_path": "..."}, ...]

    Model: Code only (no LLM)
    """
    metadata = []

    # Mode 1: PDFs directly in raw_dir
    for pdf_path in cfg.raw_dir.glob("*.pdf"):
        meta = _extract_metadata_full_book(pdf_path)
        if meta:
            metadata.append(meta)

    # Mode 2: PDFs in subdirectories
    for subdir in cfg.raw_dir.iterdir():
        if subdir.is_dir():
            for pdf_path in subdir.glob("*.pdf"):
                meta = _extract_metadata_chapter(pdf_path, subdir)
                if meta:
                    metadata.append(meta)

    # Write output
    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "ingest_metadata.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)


def _extract_metadata_full_book(pdf_path: Path) -> dict | None:
    """Extract metadata from full book PDF."""
    stem = pdf_path.stem
    parts = stem.split("_", 1)
    if len(parts) != 2:
        return None

    subject, book = parts
    exam = _detect_exam(subject)
    if exam is None:
        logger.warning("Unrecognised subject '%s' in %s — skipping", subject, pdf_path.name)
        return None

    return {
        "exam": exam.value,
        "book": book,
        "subject": subject,
        "chapter_num": None,
        "chapter_title": None,
        "input_mode": "full_book",
        "pdf_path": str(pdf_path.absolute()),
    }


def _extract_metadata_chapter(pdf_path: Path, subdir: Path) -> dict | None:
    """Extract metadata from chapter PDF in subdirectory."""
    subdir_name = subdir.name
    parts = subdir_name.split("_", 1)
    if len(parts) != 2:
        return None

    subject, book = parts
    exam = _detect_exam(subject)
    if exam is None:
        logger.warning("Unrecognised subject '%s' in %s — skipping", subject, pdf_path.name)
        return None

    stem = pdf_path.stem
    if not stem.startswith("Ch"):
        return None

    # Extract chapter number from ChNN format
    chapter_part = stem.split("_", 1)[0]
    try:
        chapter_num = int(chapter_part[2:])
    except (ValueError, IndexError):
        return None

    # Extract chapter title (remainder after ChNN_)
    if "_" in stem:
        raw_title = stem.split("_", 1)[1]
        chapter_title = re.sub(r"(?<!^)(?=[A-Z])", " ", raw_title)
    else:
        chapter_title = ""

    return {
        "exam": exam.value,
        "book": book,
        "subject": subject,
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "input_mode": "manual_chapter",
        "pdf_path": str(pdf_path.absolute()),
    }


def _detect_exam(subject: str) -> Exam | None:
    """Detect exam type from subject prefix."""
    if subject in UPPSC_SUBJECTS:
        return Exam.UPPSC
    elif subject in ["JAIIB", "CAIIB"]:
        return Exam.JAIIB_CAIIB
    else:
        return None
