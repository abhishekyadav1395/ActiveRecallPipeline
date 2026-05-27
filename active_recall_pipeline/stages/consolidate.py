from __future__ import annotations

import json
import logging
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig
from active_recall_pipeline.utils.api import call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    CONSOLIDATE — Transform raw SURVEY concepts into clean structured inventory.

    Input: config.interim_dir/survey_concepts.json
    Output: config.interim_dir/consolidated_concepts.json

    For each section, send concept list to Haiku which performs:
    - DROP: remove non-testable items
    - KEEP: mark standalone concepts
    - CLUSTER: group related items under parent

    Model: Claude Haiku
    """
    survey_file = cfg.interim_dir / "survey_concepts.json"
    with open(survey_file, encoding="utf-8") as f:
        survey_results = json.load(f)

    # Load system prompt
    system_file = cfg.prompts_dir / "consolidate_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_template = f.read()

    # Prepend CID context preamble if available
    system_prompt = (cfg.context_preamble + "\n" + system_template).strip()

    consolidated_results = []

    for section in survey_results:
        response = None
        try:
            # Build numbered concept list
            concept_list = "\n".join(
                f"{i+1}. {concept}"
                for i, concept in enumerate(section["concepts"])
            )

            # Build user prompt
            user_prompt = (
                f"SUBJECT: {section['subject']}\n"
                f"BOOK: {section['book']}\n"
                f"CHAPTER: {section['chapter_title']}\n"
                f"SECTION NUMBER: {section['section_id']}\n"
                f"\nRAW CONCEPT LIST FROM SURVEY:\n{concept_list}\n"
                f"\nConsolidate the above into a clean structured inventory.\n"
                f"Drop metadata. Keep all substantive standalone concepts.\n"
                f"Cluster grouped sub-points under their parent.\n"
                f"The output count is determined entirely by the content.\n"
            )

            # Call Haiku
            response = call_haiku(system_prompt, user_prompt, stage="CONSOLIDATE", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)

            # Parse JSON response
            concepts = _parse_and_validate_json(response)

            # Convert under-populated CLUSTERs to STANDALONE
            for concept in concepts:
                if concept.get("type") == "CLUSTER" and len(concept.get("children", [])) < 2:
                    concept["type"] = "STANDALONE"
                    concept["children"] = []

            # Re-number ids sequentially
            for i, concept in enumerate(concepts, 1):
                concept["id"] = i

            consolidated_results.append({
                "section_id": section["section_id"],
                "chapter_num": section["chapter_num"],
                "chapter_title": section["chapter_title"],
                "exam": section["exam"],
                "subject": section["subject"],
                "book": section["book"],
                "concepts": concepts,
            })

        except Exception as e:
            logger.warning(
                f"Error consolidating section {section.get('section_id', '?')}: {e}",
                exc_info=True
            )

            # Save raw response to errors directory
            if response:
                _save_error_response(cfg, section.get("section_id"), response)

            # Add entry with empty concepts
            consolidated_results.append({
                "section_id": section.get("section_id"),
                "chapter_num": section.get("chapter_num"),
                "chapter_title": section.get("chapter_title"),
                "exam": section.get("exam"),
                "subject": section.get("subject"),
                "book": section.get("book"),
                "concepts": [],
            })

    # Renumber all concept ids globally across all sections
    global_id = 1
    for section in consolidated_results:
        for concept in section["concepts"]:
            concept["id"] = global_id
            global_id += 1

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "consolidated_concepts.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(consolidated_results, f, indent=2)


def _parse_and_validate_json(response: str) -> list[dict]:
    """Parse and validate JSON response from Haiku."""
    # Strip markdown fences
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    # Parse JSON
    data = json.loads(response)

    # Validate and normalize
    concepts = []
    for item in data:
        if not isinstance(item, dict):
            continue

        # Validate required fields
        if not all(k in item for k in ["id", "text", "type", "children"]):
            logger.warning(f"Skipping concept with missing fields: {item}")
            continue

        # Validate type
        if item["type"] not in ["STANDALONE", "CLUSTER"]:
            logger.warning(f"Skipping concept with invalid type '{item['type']}'")
            continue

        # Validate children is list
        if not isinstance(item["children"], list):
            logger.warning(f"Skipping concept with non-list children: {item}")
            continue

        concepts.append({
            "id": item["id"],
            "text": str(item["text"]),
            "type": item["type"],
            "children": item["children"],
        })

    return concepts


def _save_error_response(cfg: PipelineConfig, section_id, response: str) -> None:
    """Save raw response for debugging when parsing fails."""
    error_dir = cfg.interim_dir / "consolidate_errors"
    error_dir.mkdir(parents=True, exist_ok=True)

    error_file = error_dir / f"section_{section_id}_raw.txt"
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(response)
