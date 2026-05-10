from __future__ import annotations

import json
import logging

from active_recall_pipeline.config import PipelineConfig
from active_recall_pipeline.utils.api import call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    TIER — Classify each concept: Simple/Medium/Complex.

    Input: config.interim_dir/consolidated_concepts.json
    Output: config.interim_dir/tiered_concepts.json

    For each concept, classify complexity tier based on
    dependency layers and domain connectivity.

    Model: Claude Haiku
    """
    concepts_file = cfg.interim_dir / "consolidated_concepts.json"
    with open(concepts_file) as f:
        sections = json.load(f)

    # Load system prompt
    system_file = cfg.prompts_dir / "tier_system.txt"
    with open(system_file) as f:
        system_prompt = f.read()

    tiered_sections = []

    for section in sections:
        try:
            # Build numbered concept list (id and text only)
            concept_list = "\n".join(
                f"{concept['id']}. {concept['text']}"
                for concept in section["concepts"]
            )

            # Build user prompt
            user_prompt = (
                f"Classify each concept from chapter {section['chapter_title']}, "
                f"{section['book']} (Subject: {section['subject']}).\n\n"
                f"{concept_list}"
            )

            # Call Haiku
            response = call_haiku(system_prompt, user_prompt, stage="TIER", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)

            # Parse tier response
            tier_map = _parse_tier_response(response)

            # Merge tiers onto concepts, defaulting to MEDIUM
            tiered_concepts = []
            for concept in section["concepts"]:
                concept_copy = concept.copy()
                concept_copy["tier"] = tier_map.get(concept["id"], "MEDIUM")
                tiered_concepts.append(concept_copy)

            tiered_sections.append({
                "section_id": section["section_id"],
                "chapter_num": section["chapter_num"],
                "chapter_title": section["chapter_title"],
                "exam": section["exam"],
                "subject": section["subject"],
                "book": section["book"],
                "concepts": tiered_concepts,
            })

        except Exception as e:
            logger.warning(
                f"Error tiering section {section.get('section_id', '?')}: {e}",
                exc_info=True
            )

            # Default all concepts to MEDIUM tier
            tiered_concepts = []
            for concept in section["concepts"]:
                concept_copy = concept.copy()
                concept_copy["tier"] = "MEDIUM"
                tiered_concepts.append(concept_copy)

            tiered_sections.append({
                "section_id": section.get("section_id"),
                "chapter_num": section.get("chapter_num"),
                "chapter_title": section.get("chapter_title"),
                "exam": section.get("exam"),
                "subject": section.get("subject"),
                "book": section.get("book"),
                "concepts": tiered_concepts,
            })

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "tiered_concepts.json"
    with open(output_file, "w") as f:
        json.dump(tiered_sections, f, indent=2)


def _parse_tier_response(response: str) -> dict[int, str]:
    """Parse tier response from Haiku."""
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

    # Build id -> tier mapping
    tier_map = {}
    for item in data:
        if isinstance(item, dict) and "id" in item and "tier" in item:
            tier = item["tier"].upper()
            if tier in ["SIMPLE", "MEDIUM", "COMPLEX"]:
                tier_map[item["id"]] = tier

    return tier_map
