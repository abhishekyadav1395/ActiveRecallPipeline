from __future__ import annotations

import json
import logging
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig, Exam
from active_recall_pipeline.utils.api import call_haiku


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    SURVEY — Extract every surface concept from section text.

    Input: config.interim_dir/parsed_sections.json
    Output: config.interim_dir/survey_concepts.json

    For each section, load the subject profile, inject domain-specific
    extraction guidance, call Haiku, and parse the concept list.

    Model: Claude Haiku
    Profile-aware: Yes — injects profile.survey_addition at {{DOMAIN_SPECIFIC_EXTRACTION}}
    """
    sections_file = cfg.interim_dir / "parsed_sections.json"
    with open(sections_file, encoding="utf-8") as f:
        sections_list = json.load(f)

    # Load ingest metadata to get exam, subject, book
    metadata_file = cfg.interim_dir / "ingest_metadata.json"
    with open(metadata_file, encoding="utf-8") as f:
        metadata_list = json.load(f)

    # Build lookup: pdf_path -> metadata
    metadata_by_path = {m["pdf_path"]: m for m in metadata_list}

    # Load system prompt template
    system_file = cfg.prompts_dir / "survey_system.txt"
    with open(system_file, encoding="utf-8") as f:
        system_template = f.read()

    survey_results = []

    for section in sections_list:
        try:
            # Get metadata from ingest by matching pdf_path
            pdf_path = section["pdf_path"]
            metadata = metadata_by_path.get(pdf_path)
            if not metadata:
                logger.warning(f"No metadata found for pdf_path: {pdf_path}")
                continue

            exam = Exam(metadata["exam"])
            subject = metadata["subject"]
            book = metadata["book"]

            # Load profile and inject domain-specific extraction
            profile = _load_profile(exam, cfg)
            system_prompt = system_template.replace(
                "{{DOMAIN_SPECIFIC_EXTRACTION}}",
                profile["survey_addition"]
            )

            # Build user prompt with template replacements
            user_prompt = (
                f"Extract every concept from the following section of {section['chapter_title']}\n"
                f"from {book} (Subject: {subject}).\n\n"
                f"--- BEGIN SECTION TEXT ---\n"
                f"{section['text']}\n"
                f"--- END SECTION TEXT ---\n"
            )

            # Call Haiku and parse response
            response = call_haiku(system_prompt, user_prompt, stage="SURVEY")
            concepts = _parse_concepts(response)

            survey_results.append({
                "section_id": section["section_id"],
                "chapter_num": section["chapter_num"],
                "chapter_title": section["chapter_title"],
                "exam": metadata["exam"],
                "subject": subject,
                "book": book,
                "concepts": concepts,
            })

        except Exception as e:
            logger.error(
                f"Error processing section {section.get('section_id', '?')}: {e}",
                exc_info=True
            )
            survey_results.append({
                "section_id": section.get("section_id"),
                "chapter_num": section.get("chapter_num"),
                "chapter_title": section.get("chapter_title"),
                "exam": section.get("exam"),
                "subject": "",
                "book": "",
                "concepts": [],
            })

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    output_file = cfg.interim_dir / "survey_concepts.json"
    with open(output_file, "w") as f:
        json.dump(survey_results, f, indent=2)


def _load_profile(exam: Exam, cfg: PipelineConfig) -> dict:
    """Load subject profile JSON based on exam type."""
    if exam == Exam.UPPSC:
        profile_file = cfg.profiles_dir / "uppsc_profile.json"
    else:
        profile_file = cfg.profiles_dir / "jaiib_caiib_profile.json"

    with open(profile_file) as f:
        return json.load(f)


def _parse_concepts(response: str) -> list[str]:
    """Parse numbered concept list from Haiku response."""
    concepts = []
    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Remove leading "N. " or "N) " pattern
        if line and line[0].isdigit():
            for sep in [".", ")"]:
                if sep in line:
                    parts = line.split(sep, 1)
                    concept = parts[1].strip() if len(parts) > 1 else line
                    if concept:
                        concepts.append(concept)
                    break
        elif line:
            concepts.append(line)

    return concepts
