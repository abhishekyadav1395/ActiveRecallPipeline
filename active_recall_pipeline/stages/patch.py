from __future__ import annotations

import json
import logging

from active_recall_pipeline.config import DEFAULT_CONFIG, PipelineConfig
from active_recall_pipeline.utils.api import build_batches, call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    PATCH — Generate targeted questions for gaps identified by AUDIT.

    Input: config.interim_dir/audit_report.json
           config.interim_dir/excavated_concepts.json
    Output: config.interim_dir/patched_questions.json

    Uses dynamic batching to minimize API calls.
    Model: Claude Haiku
    """
    audit_file = cfg.interim_dir / "audit_report.json"
    with open(audit_file, encoding="utf-8") as f:
        audit_report = json.load(f)

    concepts_file = cfg.interim_dir / "excavated_concepts.json"
    with open(concepts_file, encoding="utf-8") as f:
        sections_by_id = {s["section_id"]: s for s in json.load(f)}

    forge_file = cfg.interim_dir / "forge_questions.json"
    with open(forge_file, encoding="utf-8") as f:
        forge_questions = json.load(f)

    system_file = cfg.prompts_dir / "patch_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_prompt = f.read()

    gap_concepts = audit_report["gaps"]

    if not gap_concepts:
        logger.info("No gaps to patch")
        all_questions = forge_questions
    else:
        subject = gap_concepts[0].get("subject", "")
        book = gap_concepts[0].get("book", "")
        chapter_title = gap_concepts[0].get("chapter_title", "")

        user_prompt_template = (
            "SUBJECT: " + subject + " | BOOK: " + book + " | "
            "CHAPTER: " + chapter_title + "\n\n"
            "UNCOVERED CONCEPTS:\n{GAP_CONCEPTS}\n\n"
            "Generate exactly one MCQ for EVERY concept listed above. "
            "Every concept id in the list must appear in your output JSON. "
            "Do not skip any concept."
        )

        # tokens_per_output_item=500 ensures output never exceeds 64000 tokens
        # 64000 * 0.95 / 500 = ~121 concepts max per batch
        # For 319 gaps this produces ~3 batches — minimum possible
        batches = build_batches(
            concepts=gap_concepts,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            placeholder="{GAP_CONCEPTS}",
            model=DEFAULT_CONFIG.model_sonnet,
            tokens_per_output_item=500,
        )

        logger.info(f"PATCH: {len(gap_concepts)} gaps split into {len(batches)} batches")

        patch_questions = []

        for batch_num, batch in enumerate(batches):
            response = None
            try:
                batch_json = json.dumps(batch, indent=2)
                user_prompt = user_prompt_template.replace(
                    "{GAP_CONCEPTS}", batch_json
                )

                response = call_haiku(system_prompt, user_prompt, stage="PATCH", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)
                questions = _parse_patch_response(response)

                # Ensure GapFill::true tag on every patch question
                for q in questions:
                    if "GapFill::true" not in str(q.get("tags", "")):
                        q["tags"] = str(q.get("tags", "")) + " GapFill::true"

                for q in questions:
                    gap_id = q.get("inventory_id")
                    matching_gap = next(
                        (g for g in batch if g["id"] == gap_id),
                        batch[0]
                    )
                    q["section_id"] = matching_gap.get("section_id")
                    q["chapter_num"] = matching_gap.get("chapter_num")
                    q["chapter_title"] = matching_gap.get("chapter_title")
                    q["subject"] = matching_gap.get("subject")
                    q["book"] = matching_gap.get("book")
                    q["exam"] = matching_gap.get("exam")

                patch_questions.extend(questions)
                logger.info(
                    f"Batch {batch_num + 1}/{len(batches)}: "
                    f"{len(questions)} questions generated"
                )

            except Exception as e:
                logger.warning(
                    f"Error processing batch {batch_num}: {e}",
                    exc_info=True
                )
                if response:
                    error_dir = cfg.interim_dir / "patch_errors"
                    error_dir.mkdir(parents=True, exist_ok=True)
                    error_file = error_dir / f"batch_{batch_num}_raw.txt"
                    with open(error_file, "w", encoding="utf-8") as f:
                        f.write(response)

        all_questions = forge_questions + patch_questions

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    patched_file = cfg.interim_dir / "patched_questions.json"
    with open(patched_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2)

    covered_ids = {
        q.get("inventory_id")
        for q in all_questions
        if q.get("inventory_id") is not None
    }

    total_gaps = len(gap_concepts) if gap_concepts else 0
    remaining_gaps = sum(
        1 for gap in (gap_concepts or [])
        if gap["id"] not in covered_ids
    )

    logger.info(
        f"PATCH complete: {total_gaps} gaps identified, "
        f"{remaining_gaps} remaining after patching"
    )


def _sanitize_json_strings(response: str) -> str:
    """
    Fix literal newlines and tabs inside JSON string values.
    Haiku sometimes outputs real newlines inside strings instead of \\n.
    """
    fixed = []
    in_string = False
    i = 0
    while i < len(response):
        c = response[i]
        if c == '"' and (i == 0 or response[i-1] != '\\'):
            in_string = not in_string
            fixed.append(c)
        elif c == '\n' and in_string:
            fixed.append('\\n')
        elif c == '\t' and in_string:
            fixed.append('\\t')
        elif c == '\r' and in_string:
            fixed.append('\\r')
        else:
            fixed.append(c)
        i += 1
    return ''.join(fixed)


def _parse_patch_response(response: str) -> list[dict]:
    """Parse patch response from Haiku."""
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    response = _sanitize_json_strings(response)

    data = json.loads(response)
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []

    return data