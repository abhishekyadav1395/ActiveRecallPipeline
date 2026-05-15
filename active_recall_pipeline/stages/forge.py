from __future__ import annotations

import json
import logging

from active_recall_pipeline.config import DEFAULT_CONFIG, PipelineConfig, Exam
from active_recall_pipeline.utils.api import build_batches, call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    FORGE — Generate all MCQs across all 7 layers.

    Input: config.interim_dir/excavated_concepts.json
           config.interim_dir/parsed_sections.json
    Output: config.interim_dir/forge_questions.json

    Model: Claude Haiku
    Profile-aware: Yes — injects profile.forge_lineage
    """
    concepts_file = cfg.interim_dir / "excavated_concepts.json"
    with open(concepts_file, encoding="utf-8") as f:
        excavated_sections = json.load(f)

    parsed_file = cfg.interim_dir / "parsed_sections.json"
    with open(parsed_file, encoding="utf-8") as f:
        parsed_sections = json.load(f)

    parsed_by_id = {s["section_id"]: s["text"] for s in parsed_sections}

    system_file = cfg.prompts_dir / "forge_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_template = f.read()

    all_questions = []

    for section in excavated_sections:
        try:
            exam = Exam(section["exam"])
            profile = _load_profile(exam, cfg)

            if not section["concepts"]:
                logger.warning(
                    f"Section {section.get('section_id', '?')}: "
                    f"no concepts found — skipping. "
                    f"Re-run EXCAVATE for this chapter to regenerate."
                )
                continue

            system_prompt = system_template.replace(
                "{{LINEAGE_GUIDANCE}}", profile["forge_lineage"]
            )

            section_text = parsed_by_id.get(section["section_id"], "")

            # User prompt template with placeholder for concept batch
            user_prompt_template = (
                f"SUBJECT: {section['subject']} | BOOK: {section['book']} | "
                f"CHAPTER: {section['chapter_title']} | SECTION: {section['section_id']}\n\n"
                f"--- SECTION TEXT (context only) ---\n{section_text}\n--- END ---\n\n"
                f"--- COMPLETE CONCEPT INVENTORY ---\n{{{{INVENTORY}}}}\n--- END ---\n\n"
                f"Generate questions for every concept following all rules.\n"
                f"Concepts with source='decomposition' → start at Layer 1 Foundation.\n"
                f"CLUSTER type concepts → exactly one Format B statement question from children.\n"
                f"All other STANDALONE concepts → start at Layer 2 Surface."
            )

            # Build batches — split by both input and output limits
            batches = build_batches(
                concepts=section["concepts"],
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                placeholder="{{INVENTORY}}",
                model=DEFAULT_CONFIG.model_haiku,
                tokens_per_output_item=600,
            )

            logger.info(
                f"Section {section['section_id']}: "
                f"{len(section['concepts'])} concepts → {len(batches)} batches"
            )

            section_questions = []

            for batch_num, batch in enumerate(batches):
                response = None
                try:
                    batch_json = json.dumps(batch, indent=2)
                    user_prompt = user_prompt_template.replace(
                        "{{INVENTORY}}", batch_json
                    )

                    response = call_haiku(system_prompt, user_prompt, stage="FORGE", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)
                    questions = _parse_forge_response(response)

                    for q in questions:
                        q["section_id"] = section["section_id"]
                        q["chapter_num"] = section["chapter_num"]
                        q["chapter_title"] = section["chapter_title"]
                        q["subject"] = section["subject"]
                        q["book"] = section["book"]
                        q["exam"] = section["exam"]

                    section_questions.extend(questions)

                except Exception as e:
                    logger.warning(
                        f"Error forging section {section.get('section_id', '?')} "
                        f"batch {batch_num}: {e}",
                        exc_info=True
                    )
                    if response:
                        _save_error_response(
                            cfg, section.get("section_id"), response, batch_num
                        )
                    continue

            logger.info(
                f"Section {section['section_id']}: "
                f"{len(section_questions)} questions generated"
            )
            all_questions.extend(section_questions)

        except Exception as e:
            logger.warning(
                f"Error processing section {section.get('section_id', '?')}: {e}",
                exc_info=True
            )
            continue

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "forge_questions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2)

    logger.info(f"FORGE complete: {len(all_questions)} total questions")


def _load_profile(exam: Exam, cfg: PipelineConfig) -> dict:
    if exam == Exam.UPPSC:
        profile_file = cfg.profiles_dir / "uppsc_profile.json"
    else:
        profile_file = cfg.profiles_dir / "jaiib_caiib_profile.json"

    with open(profile_file, encoding="utf-8") as f:
        return json.load(f)


def _sanitize_json_strings(response: str) -> str:
    """
    Fix literal newlines and tabs inside JSON string values.
    Haiku sometimes outputs real newlines inside strings instead of escaped \\n.
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


def _parse_forge_response(response: str) -> list[dict]:
    """Parse forge response from Haiku."""
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    response = _sanitize_json_strings(response)

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        try:
            import json_repair
            data = json_repair.loads(response)
        except ImportError:
            raise json.JSONDecodeError(
                "JSON parse failed and json_repair not available. "
                "Install with: pip install json-repair",
                response, 0
            )
        except Exception as e:
            raise json.JSONDecodeError(str(e), response, 0)

    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []

    required_keys = {"q_id", "inventory_id", "layer", "format",
                     "difficulty", "question", "answer", "tags"}
    questions = []

    for item in data:
        if not isinstance(item, dict):
            continue
        if not required_keys.issubset(item.keys()):
            missing = required_keys - set(item.keys())
            logger.warning(f"Skipping question missing keys: {missing}")
            continue
        questions.append(item)

    return questions


def _save_error_response(
    cfg: PipelineConfig,
    section_id,
    response: str,
    batch_num: int = 0
) -> None:
    error_dir = cfg.interim_dir / "forge_errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    error_file = error_dir / f"section_{section_id}_batch_{batch_num}_raw.txt"
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(response)