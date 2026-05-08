#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from active_recall_pipeline.config import STAGE_ORDER
from active_recall_pipeline.utils.db import SQLiteManager


INTERIM = {
    "INGEST": "active_recall_pipeline/data/interim/ingest_metadata.json",
    "PARSE": "active_recall_pipeline/data/interim/parsed_sections.json",
    "SURVEY": "active_recall_pipeline/data/interim/survey_concepts.json",
    "CONSOLIDATE": "active_recall_pipeline/data/interim/consolidated_concepts.json",
    "TIER": "active_recall_pipeline/data/interim/tiered_concepts.json",
    "EXCAVATE": "active_recall_pipeline/data/interim/excavated_concepts.json",
    "FORGE": "active_recall_pipeline/data/interim/forge_questions.json",
    "AUDIT": "active_recall_pipeline/data/interim/audit_report.json",
    "COVERAGE": "active_recall_pipeline/data/interim/coverage_map.json",
    "PATCH": "active_recall_pipeline/data/interim/patched_questions.json",
    "MINT": "active_recall_pipeline/data/interim/minted_questions.json",
}


def check_input_file_exists(stage: str, base_path: Path) -> bool:
    """Return True if the input file for this stage exists and is non-zero."""
    if stage not in INTERIM:
        return False

    file_path = base_path / INTERIM[stage]
    return file_path.exists() and file_path.stat().st_size > 0


def format_stage_status(status: str, validation_status: str = None) -> str:
    """Return symbol and formatted status string."""
    symbol_map = {
        "completed": "✅",
        "failed": "❌",
        "running": "🔄",
        "pending": "⏸",
    }
    symbol = symbol_map.get(status, "?")

    if status == "completed" and validation_status and validation_status != "passed":
        return f"⚠️ {status}"

    return f"{symbol} {status}"


def print_chapter_detail(db: SQLiteManager, chapter_id: int, chapter_data: dict) -> tuple[bool, list[str]]:
    """Print detailed stage report for one chapter. Return (has_failures, failures_list)."""
    pdf_path = chapter_data.get("pdf_path", "?")
    parts = pdf_path.rsplit("/", 1)
    display_name = parts[-1] if parts else pdf_path

    print(f"\nChapter {chapter_id}: {display_name}")

    has_failures = False
    failures = []

    for stage in STAGE_ORDER:
        stage_row = db.get_stage_status(chapter_id, stage.value)
        if not stage_row:
            continue

        status = stage_row.get("status", "pending")
        validation_status = stage_row.get("validation_status", "pending")
        error_msg = stage_row.get("error_message")
        validation_errors_json = stage_row.get("validation_errors")
        retry_count = stage_row.get("retry_count", 0)

        stage_name = stage.value.ljust(12)
        status_str = format_stage_status(status, validation_status)
        validation_str = f"| validation: {validation_status}"

        line = f"  {stage_name} {status_str} {validation_str}"

        if status == "failed" and retry_count > 0:
            line += f" | retries: {retry_count}/3"
            has_failures = True
            failures.append((stage.value, error_msg))

        print(line)

        if status == "failed" and error_msg:
            print(f"               Error: {error_msg}")

        if validation_status == "failed" and validation_errors_json:
            try:
                validation_errors = json.loads(validation_errors_json)
                if isinstance(validation_errors, list) and validation_errors:
                    for i, err in enumerate(validation_errors[:3]):
                        print(f"               Error: {err}")
                    if len(validation_errors) > 3:
                        print(f"               ... and {len(validation_errors) - 3} more errors")
            except (json.JSONDecodeError, TypeError):
                pass

    return has_failures, failures


def print_full_report(db: SQLiteManager, base_path: Path) -> int:
    """Print full audit report. Return 0 if all passed, 1 if failures found."""
    chapters = db.get_all_chapters()
    if not chapters:
        print("No chapters found in database.")
        return 0

    completed_count = 0
    in_progress_count = 0
    failed_count = 0

    for chapter in chapters:
        status = chapter.get("status")
        if status == "completed":
            completed_count += 1
        elif status == "failed":
            failed_count += 1
        else:
            in_progress_count += 1

    total = len(chapters)

    print("Active Recall Pipeline — Audit Report")
    print("=" * 70)
    print(
        f"Chapters: {total} total | {completed_count} completed | "
        f"{in_progress_count} in progress | {failed_count} failed"
    )

    has_any_failures = False
    for chapter in chapters:
        chapter_id = chapter.get("id")
        chapter_has_failures, _ = print_chapter_detail(db, chapter_id, chapter)
        if chapter_has_failures:
            has_any_failures = True

    print("\n" + "=" * 70)
    print("Cost Summary")

    cost_summary = db.get_pipeline_summary()
    total_cost = 0.0
    for provider, data in sorted(cost_summary.items()):
        in_tokens = data.get("input_tokens", 0)
        out_tokens = data.get("output_tokens", 0)
        cost = data.get("cost_usd", 0.0)
        total_cost += cost
        print(f"  {provider:12}: ${cost:8.4f}  ({in_tokens:,} in / {out_tokens:,} out tokens)")

    print(f"  {'TOTAL':12}: ${total_cost:8.4f}")

    print("\nInterim files present:")
    for stage in STAGE_ORDER:
        if stage.value not in INTERIM:
            continue

        exists = check_input_file_exists(stage.value, base_path)
        symbol = "✅" if exists else "❌"
        filename = Path(INTERIM[stage.value]).name
        status_text = "missing" if not exists else ""
        print(f"  {symbol} {filename} {status_text}".rstrip())

    return 1 if has_any_failures else 0


def print_chapter_report(db: SQLiteManager, chapter_id: int, base_path: Path) -> int:
    """Print audit report for one chapter. Return 0 if passed, 1 if failures."""
    chapter_data = None
    all_chapters = db.get_all_chapters()

    for ch in all_chapters:
        if ch.get("id") == chapter_id:
            chapter_data = ch
            break

    if not chapter_data:
        print(f"Chapter {chapter_id} not found.")
        return 1

    has_failures, _ = print_chapter_detail(db, chapter_id, chapter_data)

    cost_summary = db.get_chapter_cost_summary(chapter_id)
    if cost_summary:
        print("\nCost Summary for this Chapter")
        for provider, data in sorted(cost_summary.items()):
            in_tokens = data.get("input_tokens", 0)
            out_tokens = data.get("output_tokens", 0)
            cost = data.get("cost_usd", 0.0)
            print(f"  {provider:12}: ${cost:8.4f}  ({in_tokens:,} in / {out_tokens:,} out tokens)")

    return 1 if has_failures else 0


def do_fix(db: SQLiteManager) -> int:
    """Reset all failed stages to pending. Return count of resets."""
    reset_count = 0

    all_chapters = db.get_all_chapters()
    for chapter in all_chapters:
        chapter_id = chapter.get("id")

        for stage in STAGE_ORDER:
            stage_status = db.get_stage_status(chapter_id, stage.value)
            if not stage_status:
                continue

            if stage_status.get("status") == "failed":
                db.set_stage_status(chapter_id, stage.value, "pending", error_message=None)
                db.set_validation_status(chapter_id, stage.value, "pending", validation_errors=None)
                print(f"  Reset: Chapter {chapter_id} / {stage.value} → pending")
                reset_count += 1

    print(f"\nTotal resets: {reset_count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit and validate the Active Recall Pipeline"
    )
    parser.add_argument(
        "--chapter",
        type=int,
        default=None,
        help="Audit only this chapter ID"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Reset all failed stages to pending"
    )

    args = parser.parse_args()

    base_path = Path(__file__).parent.parent
    db = SQLiteManager(base_path / "data" / "pipeline.db")

    if args.fix:
        return do_fix(db)

    if args.chapter is not None:
        return print_chapter_report(db, args.chapter, base_path)

    return print_full_report(db, base_path)


if __name__ == "__main__":
    sys.exit(main())
