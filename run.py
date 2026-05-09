from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig, Stage, STAGE_ORDER
from active_recall_pipeline.pipeline import PipelineOrchestrator
from active_recall_pipeline.stages.ingest import _extract_metadata_full_book, _extract_metadata_chapter
from active_recall_pipeline.utils.db import SQLiteManager


logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for the pipeline."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Active Recall Pipeline — Generate MCQs from textbooks"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="INGEST",
        help="Starting stage (default: INGEST)",
    )
    parser.add_argument(
        "--stop",
        type=str,
        default="DELIVER",
        help="Stopping stage (default: DELIVER)",
    )
    parser.add_argument(
        "--skip",
        type=str,
        action="append",
        default=[],
        help="Stages to skip (can be repeated)",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        return 1

    # Create config
    try:
        start_stage = Stage(args.start.upper())
        stop_stage = Stage(args.stop.upper())
        skip_stages = [Stage(s.upper()) for s in args.skip]
    except ValueError as e:
        print(f"ERROR: Invalid stage name: {e}", file=sys.stderr)
        return 1

    try:
        cfg = PipelineConfig(
            api_key=api_key,
            start_stage=start_stage,
            stop_stage=stop_stage,
            skip_stages=skip_stages,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Get active stages
    active_stages = cfg.active_stages()
    logger.info("Pipeline stages: %s", [s.value for s in active_stages])

    # Extract metadata from first PDF if not already set
    if not cfg.pdf_path:
        metadata = None
        # Try to find PDFs in raw_dir
        if cfg.raw_dir.exists():
            # Look for full-book PDFs first
            for pdf_path in cfg.raw_dir.glob("*.pdf"):
                metadata = _extract_metadata_full_book(pdf_path)
                if metadata:
                    break

            # If not found, look in subdirectories for chapter PDFs
            if not metadata:
                for subdir in cfg.raw_dir.iterdir():
                    if subdir.is_dir():
                        for pdf_path in subdir.glob("*.pdf"):
                            metadata = _extract_metadata_chapter(pdf_path, subdir)
                            if metadata:
                                break
                    if metadata:
                        break

        if not metadata:
            print("ERROR: No PDF files found in raw_dir", file=sys.stderr)
            return 1

        # Update config with extracted metadata
        cfg.exam = metadata["exam"]
        cfg.subject = metadata["subject"]
        cfg.book = metadata["book"]
        cfg.chapter_num = metadata["chapter_num"]
        cfg.chapter_title = metadata["chapter_title"]
        cfg.pdf_path = Path(metadata["pdf_path"])
        cfg.input_mode = metadata["input_mode"]

    # Initialize database and orchestrator
    db = SQLiteManager()

    # Register chapter if not already in DB
    chapter_id = db.upsert_chapter(
        exam=cfg.exam,
        subject=cfg.subject,
        book=cfg.book,
        chapter_num=cfg.chapter_num,
        chapter_title=cfg.chapter_title,
        pdf_path=str(cfg.pdf_path),
        input_mode=cfg.input_mode,
    )
    db.init_stage_runs(chapter_id)

    # Run orchestrator
    orchestrator = PipelineOrchestrator(cfg=cfg, db=db)
    success = orchestrator.run_chapter(chapter_id)

    if success:
        db.set_chapter_status(chapter_id, "completed")
        print(f"Pipeline complete. Output in: {cfg.output_dir}")
        return 0
    else:
        db.set_chapter_status(chapter_id, "failed")
        logger.error("Pipeline failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
