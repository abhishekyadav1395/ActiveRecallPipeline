from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig, Stage, STAGE_ORDER
from active_recall_pipeline.stages.ingest import run as ingest_run
from active_recall_pipeline.stages.parse import run as parse_run
from active_recall_pipeline.stages.survey import run as survey_run
from active_recall_pipeline.stages.consolidate import run as consolidate_run
from active_recall_pipeline.stages.tier import run as tier_run
from active_recall_pipeline.stages.excavate import run as excavate_run
from active_recall_pipeline.stages.forge import run as forge_run
from active_recall_pipeline.stages.audit import run as audit_run
from active_recall_pipeline.stages.patch import run as patch_run
from active_recall_pipeline.stages.mint import run as mint_run
from active_recall_pipeline.stages.deliver import run as deliver_run
from active_recall_pipeline.utils.db import SQLiteManager
from active_recall_pipeline.utils.validation import StageValidator, ValidationResult


logger = logging.getLogger(__name__)


STAGE_RUNNERS: dict[Stage, type] = {
    Stage.INGEST: ingest_run,
    Stage.PARSE: parse_run,
    Stage.SURVEY: survey_run,
    Stage.CONSOLIDATE: consolidate_run,
    Stage.TIER: tier_run,
    Stage.EXCAVATE: excavate_run,
    Stage.FORGE: forge_run,
    Stage.AUDIT: audit_run,
    Stage.PATCH: patch_run,
    Stage.MINT: mint_run,
    Stage.DELIVER: deliver_run,
}

INTERIM_FILES = {
    "INGEST": "ingest_metadata.json",
    "PARSE": "parsed_sections.json",
    "SURVEY": "survey_concepts.json",
    "CONSOLIDATE": "consolidated_concepts.json",
    "TIER": "tiered_concepts.json",
    "EXCAVATE": "excavated_concepts.json",
    "FORGE": "forge_questions.json",
    "AUDIT": "audit_report.json",
    "PATCH": "patched_questions.json",
    "MINT": "minted_questions.json",
}

VALIDATED_STAGES = {
    Stage.SURVEY,
    Stage.CONSOLIDATE,
    Stage.TIER,
    Stage.EXCAVATE,
    Stage.FORGE,
    Stage.PATCH,
}

MAX_RETRIES = 3
RETRY_DELAYS = [10, 30, 60]  # seconds between attempts


def _ensure_dirs(cfg: PipelineConfig) -> None:
    for d in (cfg.raw_dir, cfg.interim_dir, cfg.output_dir, cfg.artifacts_dir, cfg.logs_dir):
        d.mkdir(parents=True, exist_ok=True)


class PipelineOrchestrator:
    def __init__(self, cfg: PipelineConfig, db: SQLiteManager):
        self.cfg = cfg
        self.db = db
        self.validator = StageValidator()

    def run_chapter(self, chapter_id: int) -> bool:
        """Run all pending stages for one chapter. Return True if all passed."""
        _ensure_dirs(self.cfg)

        active_stages = self.cfg.active_stages()
        logger.info("Running %d active stages: %s", len(active_stages), [s.value for s in active_stages])

        for stage in active_stages:
            # Check if stage already completed and passed (resume support)
            if self.db.stage_completed(chapter_id, stage.value):
                print(f"[{stage.value:12}] skipped (already completed)")
                continue

            # Run stage with retry logic
            success = self.run_stage(chapter_id, stage)
            if not success:
                logger.error("[%s] failed after %d attempts, stopping chapter", stage.value, MAX_RETRIES)
                return False

        logger.info("Chapter %d completed successfully", chapter_id)
        return True

    def run_stage(self, chapter_id: int, stage: Stage) -> bool:
        """Run one stage with retry logic. Return True if passed."""
        for attempt in range(MAX_RETRIES):
            success = self._execute_stage(chapter_id, stage)
            if success:
                return True

            retry_count = self.db.increment_retry(chapter_id, stage.value)
            if retry_count >= MAX_RETRIES:
                logger.error("[%s] failed after %d attempts", stage.value, MAX_RETRIES)
                return False

            delay = RETRY_DELAYS[attempt]
            print(f"[{stage.value:12}] retrying (attempt {attempt + 1}/{MAX_RETRIES})...")
            logger.warning(
                "[%s] attempt %d failed, retrying in %ds",
                stage.value, attempt + 1, delay
            )
            time.sleep(delay)

        return False

    def _execute_stage(self, chapter_id: int, stage: Stage) -> bool:
        """Single execution attempt. Return True if stage + validation passed."""
        try:
            # Mark as running
            self.db.set_stage_status(chapter_id, stage.value, "running")
            print(f"[{stage.value:12}] starting...")

            # Load input file
            if stage != Stage.INGEST:
                # All stages except INGEST need an input file
                prev_idx = STAGE_ORDER.index(stage) - 1
                if prev_idx >= 0:
                    prev_stage = STAGE_ORDER[prev_idx]
                    input_file = INTERIM_FILES.get(prev_stage.value)
                    if input_file:
                        input_path = self.cfg.interim_dir / input_file
                        if not input_path.exists() or input_path.stat().st_size == 0:
                            error_msg = f"Input file missing or empty: {input_file}"
                            logger.error("[%s] %s", stage.value, error_msg)
                            self.db.set_stage_status(chapter_id, stage.value, "failed", error_msg)
                            return False

            # Call stage runner
            runner = STAGE_RUNNERS[stage]
            runner(self.cfg)

            # Load output file (some stages like DELIVER may not have interim output)
            output_file = INTERIM_FILES.get(stage.value)
            output_data = None
            if output_file:
                output_path = self.cfg.interim_dir / output_file
                if not output_path.exists() or output_path.stat().st_size == 0:
                    error_msg = f"Output file missing or empty: {output_file}"
                    logger.error("[%s] %s", stage.value, error_msg)
                    self.db.set_stage_status(chapter_id, stage.value, "failed", error_msg)
                    return False

                output_data = self._load_interim(output_file)
                if output_data is None:
                    error_msg = f"Failed to parse output file: {output_file}"
                    logger.error("[%s] %s", stage.value, error_msg)
                    self.db.set_stage_status(chapter_id, stage.value, "failed", error_msg)
                    return False

            # Run validation
            validation_result = self._validate_stage(chapter_id, stage, output_data)

            if validation_result.passed:
                self.db.set_stage_status(chapter_id, stage.value, "completed")
                self.db.set_validation_status(chapter_id, stage.value, "passed")
                print(f"[{stage.value:12}] completed ✅")
                return True
            else:
                # Validation failed
                error_summary = "; ".join(validation_result.errors[:3])
                if len(validation_result.errors) > 3:
                    error_summary += f" (+{len(validation_result.errors) - 3} more)"
                logger.error("[%s] validation failed: %s", stage.value, error_summary)
                self.db.set_stage_status(
                    chapter_id, stage.value, "failed",
                    error_message=error_summary
                )
                self.db.set_validation_status(
                    chapter_id, stage.value, "failed",
                    validation_errors=validation_result.errors
                )
                print(f"[{stage.value:12}] validation failed ❌")
                for err in validation_result.errors[:3]:
                    print(f"              {err}")
                return False

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error("[%s] exception: %s", stage.value, error_msg, exc_info=True)
            self.db.set_stage_status(chapter_id, stage.value, "failed", error_message=error_msg)
            print(f"[{stage.value:12}] failed with exception ❌")
            print(f"              {error_msg}")
            return False

    def _validate_stage(self, chapter_id: int, stage: Stage, output) -> ValidationResult:
        """Run the appropriate validator and write result to SQLite."""
        # Code stages don't need validation
        if stage not in VALIDATED_STAGES:
            return ValidationResult(passed=True)

        # Build context for validator
        context = self._build_validation_context(chapter_id, stage)

        # Call the appropriate validator
        if stage == Stage.SURVEY:
            result = self.validator.validate_survey(output, context)
        elif stage == Stage.CONSOLIDATE:
            result = self.validator.validate_consolidate(output, context)
        elif stage == Stage.TIER:
            result = self.validator.validate_tier(output, context)
        elif stage == Stage.EXCAVATE:
            result = self.validator.validate_excavate(output, context)
        elif stage == Stage.FORGE:
            result = self.validator.validate_forge(output, context)
        elif stage == Stage.PATCH:
            result = self.validator.validate_patch(output, context)
        else:
            return ValidationResult(passed=True)

        return result

    def _build_validation_context(self, chapter_id: int, stage: Stage) -> dict:
        """Build the context dict required by each validator."""
        chapter = self.db.get_stage_status(chapter_id, Stage.INGEST.value)
        chapter_title = ""
        if chapter:
            # Get from chapters table
            chapters = self.db.get_all_chapters()
            for ch in chapters:
                if ch["id"] == chapter_id:
                    chapter_title = ch["chapter_title"]
                    break

        ctx = {"chapter_title": chapter_title}

        if stage == Stage.SURVEY:
            # No extra context needed
            pass

        elif stage == Stage.CONSOLIDATE:
            # No extra context needed
            pass

        elif stage == Stage.TIER:
            consolidated = self._load_interim("consolidated_concepts.json")
            if consolidated:
                ctx["consolidate_count"] = len(consolidated)
                ctx["consolidate_ids"] = [item["id"] for item in consolidated if isinstance(item, dict)]

        elif stage == Stage.EXCAVATE:
            tiered = self._load_interim("tiered_concepts.json")
            if tiered:
                ctx["non_simple_ids"] = [
                    item["id"] for item in tiered
                    if isinstance(item, dict) and item.get("tier") != "SIMPLE"
                ]

        elif stage == Stage.FORGE:
            consolidated = self._load_interim("consolidated_concepts.json")
            if consolidated:
                ctx["concept_count"] = len(consolidated)

        elif stage == Stage.PATCH:
            audit = self._load_interim("audit_report.json")
            forge_qs = self._load_interim("forge_questions.json")
            if audit and isinstance(audit, dict):
                ctx["gap_ids"] = set(audit.get("gap_ids", []))
            else:
                ctx["gap_ids"] = set()
            if forge_qs:
                ctx["existing_q_ids"] = {
                    q["q_id"] for q in forge_qs
                    if isinstance(q, dict) and "q_id" in q
                }
            else:
                ctx["existing_q_ids"] = set()

        return ctx

    def _load_interim(self, filename: str) -> list | dict | None:
        """Load a JSON file from data/interim/. Return None if missing or invalid."""
        path = self.cfg.interim_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error("Failed to parse %s: %s", filename, e)
            return None
