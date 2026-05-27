from __future__ import annotations

import json
import logging
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig
from active_recall_pipeline.utils.api import call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    SCOUT — Generate Chapter Intelligence Document (CID).

    Input: config.interim_dir/parsed_sections.json
    Output: config.interim_dir/chapter_profile.json

    Idempotent: skips LLM call if chapter_profile.json exists and is valid.

    Model: Claude Haiku (Tier 1)
    """
    output_file = cfg.interim_dir / "chapter_profile.json"

    # Check idempotency: if output exists and is valid, skip
    if output_file.exists() and output_file.stat().st_size > 0:
        try:
            with open(output_file, encoding="utf-8") as f:
                existing = json.load(f)
            if _is_valid_profile(existing):
                logger.info("chapter_profile.json already exists and is valid — skipping LLM call")
                return
        except (json.JSONDecodeError, IOError):
            logger.warning("chapter_profile.json exists but is invalid — regenerating")

    # Load parsed sections
    sections_file = cfg.interim_dir / "parsed_sections.json"
    with open(sections_file, encoding="utf-8") as f:
        sections_list = json.load(f)

    if not sections_list:
        logger.warning("No parsed sections found")
        return

    # Concatenate all section text
    all_text = "\n\n".join(
        f"--- Section {s.get('section_id', '?')} ---\n{s.get('text', '')}"
        for s in sections_list
    )

    # Load system prompt
    system_file = cfg.prompts_dir / "scout_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_prompt = f.read()

    # Build user prompt
    user_prompt = (
        f"Analyze the following chapter text and generate a Chapter Intelligence Document.\n\n"
        f"{all_text}\n"
    )

    # Call Haiku
    response = call_haiku(
        system_prompt,
        user_prompt,
        stage="SCOUT",
        cfg=cfg,
        db_logger=cfg.db_logger,
        chapter_id=cfg.chapter_id
    )

    # Parse JSON response
    profile = _parse_profile(response)
    if not profile:
        raise ValueError("Failed to parse SCOUT response as valid JSON")

    # Write to interim file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    # Persist to database
    if cfg.db_logger and cfg.chapter_id:
        cfg.db_logger.upsert_chapter_profile(cfg.chapter_id, profile)

    logger.info("Generated chapter_profile.json")


def _parse_profile(raw: str) -> dict | None:
    """Parse JSON from SCOUT response. Handle markdown fences if present."""
    if not raw or not isinstance(raw, str):
        return None

    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _is_valid_profile(profile: dict) -> bool:
    """Check if profile has all required fields."""
    required = {
        "chapter_title",
        "primary_domain",
        "structural_type",
        "core_entities",
        "dominant_themes",
        "concept_density",
        "scope_boundary",
        "natural_clusters",
    }
    return isinstance(profile, dict) and required.issubset(profile.keys())
