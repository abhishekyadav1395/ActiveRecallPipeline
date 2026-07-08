from __future__ import annotations

import json
import logging

from active_recall_pipeline.config import DEFAULT_CONFIG, PipelineConfig
from active_recall_pipeline.utils.api import build_batches, call_sonnet, call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    EXCAVATE — Build prerequisite chains per concept using batching.

    Input: config.interim_dir/tiered_concepts.json
    Output: config.interim_dir/excavated_concepts.json

    Batches concepts by tier and decomposes using extended thinking.
    MEDIUM: 2000 tokens, COMPLEX: 4000 tokens.

    Model: Claude Sonnet with extended thinking
    """
    concepts_file = cfg.interim_dir / "tiered_concepts.json"
    with open(concepts_file, encoding="utf-8") as f:
        sections = json.load(f)

    # Load system prompt
    system_file = cfg.prompts_dir / "excavate_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_prompt = f.read()

    # Prepend CID context preamble if available
    system_prompt = (cfg.context_preamble + "\n" + system_prompt).strip()

    excavated_sections = []

    for section in sections:
        excavated_concepts = [c.copy() for c in section["concepts"]]
        next_id = max((c["id"] for c in excavated_concepts), default=0) + 1

        # Separate concepts by tier (CLUSTER skipped — tested as unit, not decomposed)
        simple_concepts = [
            c for c in section["concepts"]
            if c["tier"] == "SIMPLE" and c["type"] != "CLUSTER"
        ]
        medium_concepts = [
            c for c in section["concepts"]
            if c["tier"] == "MEDIUM" and c["type"] != "CLUSTER"
        ]
        complex_concepts = [
            c for c in section["concepts"]
            if c["tier"] == "COMPLEX" and c["type"] != "CLUSTER"
        ]

        # Build existing inventory text
        existing_inventory_text = "\n".join(
            f"{c['id']}. {c['text']}"
            for c in excavated_concepts
        )


        # Process SIMPLE concepts (lightweight — 1-2 prereqs only)
        if simple_concepts:
            user_prompt_template = (
                f"SUBJECT: {section['subject']} | BOOK: {section['book']} | "
                f"CHAPTER: {section['chapter_title']}\n\n"
                f"EXISTING INVENTORY (do not add these):\n"
                f"{existing_inventory_text}\n\n"
                f"CONCEPTS TO DECOMPOSE:\n{{{{CONCEPT_BATCH}}}}\n\n"
                f"For every concept identify 1-2 direct prerequisites only. "
                f"Do not recurse deep. Every concept_id must appear in output."
            )
            batches = build_batches(
                concepts=simple_concepts,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                placeholder="{{CONCEPT_BATCH}}",
                model=DEFAULT_CONFIG.model_sonnet,
            )
            for batch_num, batch in enumerate(batches):
                response = None
                try:
                    batch_json = json.dumps(batch, indent=2)
                    user_prompt = user_prompt_template.replace("{{CONCEPT_BATCH}}", batch_json)
                    response = call_haiku(system_prompt, user_prompt, stage="EXCAVATE", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)
                    responses_array = _parse_batch_response(response)
                    for concept_response in responses_array:
                        for prereq in concept_response.get("prerequisites", []):
                            if not _is_in_inventory(prereq["text"], excavated_concepts):
                                excavated_concepts.append({
                                    "id": next_id,
                                    "text": prereq["text"],
                                    "type": "STANDALONE",
                                    "tier": "SIMPLE",
                                    "children": [],
                                    "source": "decomposition",
                                    "parent_concept_id": concept_response.get("concept_id"),
                                    "depth": prereq["depth"],
                                    "reason": prereq["reason"],
                                })
                                next_id += 1
                except Exception as e:
                    logger.warning(f"Error processing SIMPLE batch {batch_num}: {e}", exc_info=True)

        # Process MEDIUM concepts
        if medium_concepts:
            user_prompt_template = (
                f"SUBJECT: {section['subject']} | BOOK: {section['book']} | "
                f"CHAPTER: {section['chapter_title']}\n\n"
                f"EXISTING INVENTORY (do not add these):\n"
                f"{existing_inventory_text}\n\n"
                f"CONCEPTS TO DECOMPOSE:\n{{{{CONCEPT_BATCH}}}}\n\n"
                f"For every concept above identify complete prerequisite chains. "
                f"Every concept_id must appear in output."
            )

            batches = build_batches(
                concepts=medium_concepts,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                placeholder="{{CONCEPT_BATCH}}",
                model=DEFAULT_CONFIG.model_sonnet,
            )

            for batch_num, batch in enumerate(batches):
                response = None
                try:
                    batch_json = json.dumps(batch, indent=2)
                    user_prompt = user_prompt_template.replace(
                        "{{CONCEPT_BATCH}}", batch_json
                    )

                    response = call_haiku(system_prompt, user_prompt, stage="EXCAVATE", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)
                    responses_array = _parse_batch_response(response)

                    # Validate all concept_ids appear in response
                    batch_ids = {c["id"] for c in batch}
                    response_ids = {r.get("concept_id") for r in responses_array}
                    missing_ids = batch_ids - response_ids
                    if missing_ids:
                        logger.warning(
                            f"Batch {batch_num} missing concept_ids in response: {missing_ids}"
                        )

                    # Collect prerequisites
                    for concept_response in responses_array:
                        prereqs = concept_response.get("prerequisites", [])
                        for prereq in prereqs:
                            # Check if already in inventory
                            if not _is_in_inventory(prereq["text"], excavated_concepts):
                                # Assign tier based on depth
                                tier = "MEDIUM" if prereq["depth"] <= 3 else "COMPLEX"

                                excavated_concepts.append({
                                    "id": next_id,
                                    "text": prereq["text"],
                                    "type": "STANDALONE",
                                    "tier": tier,
                                    "children": [],
                                    "source": "decomposition",
                                    "parent_concept_id": concept_response.get("concept_id"),
                                    "depth": prereq["depth"],
                                    "reason": prereq["reason"],
                                })
                                next_id += 1

                except Exception as e:
                    batch_ids = [c["id"] for c in batch]
                    logger.warning(
                        f"Error processing MEDIUM batch {batch_num} "
                        f"(concept_ids {batch_ids}): {e}",
                        exc_info=True
                    )

                    # Save raw response
                    if response:
                        error_dir = cfg.interim_dir / "excavate_errors"
                        error_dir.mkdir(parents=True, exist_ok=True)
                        error_file = error_dir / f"batch_{batch_num}_raw.txt"
                        with open(error_file, "w", encoding="utf-8") as f:
                            f.write(response)

        # Rebuild inventory text to include prerequisites found during MEDIUM processing
        existing_inventory_text = "\n".join(
            f"{c['id']}. {c['text']}"
            for c in excavated_concepts
        )

        # Process COMPLEX concepts
        if complex_concepts:
            user_prompt_template = (
                f"SUBJECT: {section['subject']} | BOOK: {section['book']} | "
                f"CHAPTER: {section['chapter_title']}\n\n"
                f"EXISTING INVENTORY (do not add these):\n"
                f"{existing_inventory_text}\n\n"
                f"CONCEPTS TO DECOMPOSE:\n{{{{CONCEPT_BATCH}}}}\n\n"
                f"For every concept above identify complete prerequisite chains. "
                f"Every concept_id must appear in output."
            )

            batches = build_batches(
                concepts=complex_concepts,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                placeholder="{{CONCEPT_BATCH}}",
                model=DEFAULT_CONFIG.model_sonnet,
            )

            for batch_num, batch in enumerate(batches):
                response = None
                try:
                    batch_json = json.dumps(batch, indent=2)
                    user_prompt = user_prompt_template.replace(
                        "{{CONCEPT_BATCH}}", batch_json
                    )

                    response = call_haiku(system_prompt, user_prompt, stage="EXCAVATE", cfg=cfg, db_logger=cfg.db_logger, chapter_id=cfg.chapter_id)
                    responses_array = _parse_batch_response(response)

                    # Validate all concept_ids appear in response
                    batch_ids = {c["id"] for c in batch}
                    response_ids = {r.get("concept_id") for r in responses_array}
                    missing_ids = batch_ids - response_ids
                    if missing_ids:
                        logger.warning(
                            f"Batch {batch_num} missing concept_ids in response: {missing_ids}"
                        )

                    # Collect prerequisites
                    for concept_response in responses_array:
                        prereqs = concept_response.get("prerequisites", [])
                        for prereq in prereqs:
                            # Check if already in inventory
                            if not _is_in_inventory(prereq["text"], excavated_concepts):
                                # Assign tier based on depth
                                tier = "MEDIUM" if prereq["depth"] <= 3 else "COMPLEX"

                                excavated_concepts.append({
                                    "id": next_id,
                                    "text": prereq["text"],
                                    "type": "STANDALONE",
                                    "tier": tier,
                                    "children": [],
                                    "source": "decomposition",
                                    "parent_concept_id": concept_response.get("concept_id"),
                                    "depth": prereq["depth"],
                                    "reason": prereq["reason"],
                                })
                                next_id += 1

                except Exception as e:
                    batch_ids = [c["id"] for c in batch]
                    logger.warning(
                        f"Error processing COMPLEX batch {batch_num} "
                        f"(concept_ids {batch_ids}): {e}",
                        exc_info=True
                    )

                    # Save raw response
                    if response:
                        error_dir = cfg.interim_dir / "excavate_errors"
                        error_dir.mkdir(parents=True, exist_ok=True)
                        error_file = error_dir / f"batch_{batch_num}_raw.txt"
                        with open(error_file, "w", encoding="utf-8") as f:
                            f.write(response)

        excavated_sections.append({
            "section_id": section["section_id"],
            "chapter_num": section["chapter_num"],
            "chapter_title": section["chapter_title"],
            "exam": section["exam"],
            "subject": section["subject"],
            "book": section["book"],
            "concepts": excavated_concepts,
        })

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "excavated_concepts.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(excavated_sections, f, indent=2)


def _parse_batch_response(response: str) -> list[dict]:
    """Parse batch response from Sonnet (array of concept objects)."""
    # Strip markdown fences
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    # Parse JSON array
    data = json.loads(response)

    if not isinstance(data, list):
        logger.warning(f"Expected array response, got {type(data).__name__}")
        return []

    # Validate each object has required fields
    result = []
    for item in data:
        if isinstance(item, dict) and "concept_id" in item:
            result.append(item)

    return result


def _is_in_inventory(text: str, concepts: list[dict]) -> bool:
    """Check if text already exists in concept inventory."""
    return any(c.get("text") == text for c in concepts)
