from __future__ import annotations

import json

from active_recall_pipeline.config import PipelineConfig


def run(cfg: PipelineConfig) -> None:
    """
    AUDIT — Verify every inventory item has ≥1 question.

    Input: config.interim_dir/excavated_concepts.json
           config.interim_dir/forge_questions.json
    Output: config.interim_dir/audit_report.json
            config.interim_dir/coverage_map.json

    Model: Code only
    """
    # Load concepts and questions
    concepts_file = cfg.interim_dir / "excavated_concepts.json"
    with open(concepts_file) as f:
        sections = json.load(f)

    questions_file = cfg.interim_dir / "forge_questions.json"
    with open(questions_file) as f:
        questions = json.load(f)

    # Build coverage map: inventory_id -> [q_ids]
    coverage_map = {}
    for q in questions:
        inv_id = q.get("inventory_id")
        if inv_id is not None:
            if inv_id not in coverage_map:
                coverage_map[inv_id] = []
            coverage_map[inv_id].append(q.get("q_id"))

    # Check coverage
    total_concepts = 0
    covered_concepts = 0
    gaps = []

    for section in sections:
        for concept in section["concepts"]:
            total_concepts += 1
            concept_id = concept["id"]

            # Check coverage based on type
            is_covered = False

            if concept.get("type") == "CLUSTER":
                # CLUSTER needs exactly 1 Statement question
                if concept_id in coverage_map:
                    section_questions = [q for q in questions if q.get("inventory_id") == concept_id]
                    statement_qs = [q for q in section_questions if q.get("format") == "Statement"]
                    if statement_qs:
                        is_covered = True
            else:
                # STANDALONE needs at least 1 question
                if concept_id in coverage_map:
                    is_covered = True

            if is_covered:
                covered_concepts += 1
            else:
                gaps.append({
                    "id": concept_id,
                    "text": concept.get("text"),
                    "type": concept.get("type"),
                    "tier": concept.get("tier"),
                    "children": concept.get("children", []),
                    "section_id": section.get("section_id"),
                    "chapter_num": section.get("chapter_num"),
                    "chapter_title": section.get("chapter_title"),
                    "subject": section.get("subject"),
                    "book": section.get("book"),
                    "exam": section.get("exam"),
                })

    # Build audit report
    audit_report = {
        "total_concepts": total_concepts,
        "covered_concepts": covered_concepts,
        "gap_count": len(gaps),
        "gap_ids": [g["id"] for g in gaps],
        "gaps": gaps,
    }

    # Save outputs
    cfg.interim_dir.mkdir(parents=True, exist_ok=True)

    report_file = cfg.interim_dir / "audit_report.json"
    with open(report_file, "w") as f:
        json.dump(audit_report, f, indent=2)

    coverage_file = cfg.interim_dir / "coverage_map.json"
    with open(coverage_file, "w") as f:
        json.dump(coverage_map, f, indent=2)
