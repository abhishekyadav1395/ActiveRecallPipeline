from __future__ import annotations

import json
import logging

from active_recall_pipeline.config import PipelineConfig


logger = logging.getLogger(__name__)


def run(cfg: PipelineConfig) -> None:
    """
    MINT — Deduplicate questions using Jaccard similarity.

    Input: config.interim_dir/patched_questions.json
    Output: config.interim_dir/minted_questions.json

    Removes near-duplicate questions where question text has
    >85% Jaccard similarity. Keeps first occurrence.

    Model: Code only
    """
    # Load patched questions
    patched_file = cfg.interim_dir / "patched_questions.json"
    with open(patched_file) as f:
        questions = json.load(f)

    # Deduplicate
    minted_questions = []
    seen_indices = set()
    duplicates_removed = 0

    for i, q in enumerate(questions):
        if i in seen_indices:
            continue

        minted_questions.append(q)

        # Find duplicates of this question
        q_text = q.get("question", "").lower()
        q_words = set(q_text.split())

        for j in range(i + 1, len(questions)):
            if j in seen_indices:
                continue

            other_text = questions[j].get("question", "").lower()
            other_words = set(other_text.split())

            if _jaccard_similarity(q_words, other_words) > 0.85:
                seen_indices.add(j)
                duplicates_removed += 1

    logger.info(f"MINT: removed {duplicates_removed} duplicate questions")

    # Save minted questions
    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    minted_file = cfg.interim_dir / "minted_questions.json"
    with open(minted_file, "w") as f:
        json.dump(minted_questions, f, indent=2)


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not (set_a | set_b):
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)
