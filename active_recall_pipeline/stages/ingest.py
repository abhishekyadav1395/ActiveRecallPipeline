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

    If cfg.pdf_path is set (batch/chapter mode): process that single PDF only.
    If cfg.pdf_path is None (full book mode): scan raw_dir as before.

    Output: Metadata JSON in cfg.interim_dir/ingest_metadata.json
    """
    metadata = []

    if cfg.pdf_path is not None:
        # Chapter mode — process only the assigned PDF
        pdf_path = Path(cfg.pdf_path)
        parent = pdf_path.parent
        subdir_name = parent.name

        # Determine if it's a chapter in a subdirectory or a full book
        if "_" in subdir_name and not pdf_path.stem.startswith("Ch"):
            # Full book PDF in a named subfolder — treat as full book
            meta = _extract_metadata_full_book(pdf_path)
        elif pdf_path.stem.startswith("Ch"):
            # Chapter PDF in Subject_Book/ subfolder
            meta = _extract_metadata_chapter(pdf_path, parent)
        else:
            # Direct full book PDF
            meta = _extract_metadata_full_book(pdf_path)

        if meta:
            metadata.append(meta)
        else:
            logger.warning("Could not extract metadata from %s", cfg.pdf_path)

    else:
        # Full book mode — scan entire raw_dir
        for pdf_path in cfg.raw_dir.glob("*.pdf"):
            meta = _extract_metadata_full_book(pdf_path)
            if meta:
                metadata.append(meta)

        for subdir in cfg.raw_dir.iterdir():
            if subdir.is_dir():
                for pdf_path in subdir.glob("*.pdf"):
                    meta = _extract_metadata_chapter(pdf_path, subdir)
                    if meta:
                        metadata.append(meta)

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
