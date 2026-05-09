from __future__ import annotations

import json

from active_recall_pipeline.config import DEFAULT_CONFIG
from active_recall_pipeline.providers.router import ProviderRouter


def get_router(
    stage: str,
    cfg=None,
    db_logger=None,
) -> ProviderRouter:
    """Get a ProviderRouter for the given stage."""
    if cfg is None:
        cfg = DEFAULT_CONFIG
    return ProviderRouter(cfg=cfg, stage=stage, db_logger=db_logger)


def call_haiku(system_prompt: str, user_prompt: str,
               cfg=None, db_logger=None,
               chapter_id=None, stage: str = "SURVEY") -> str:
    """Backward-compatible wrapper. Routes through Tier 1 waterfall."""
    router = get_router(stage, cfg=cfg, db_logger=db_logger)
    return router.call(system_prompt, user_prompt,
                       max_tokens=64000, chapter_id=chapter_id)


def call_sonnet(system_prompt: str, user_prompt: str,
                thinking_budget: int = 0,
                cfg=None, db_logger=None,
                chapter_id=None, stage: str = "EXCAVATE") -> str:
    """Backward-compatible wrapper. Routes through Tier 2 waterfall."""
    router = get_router(stage, cfg=cfg, db_logger=db_logger)
    return router.call(system_prompt, user_prompt,
                       max_tokens=64000,
                       thinking_budget=thinking_budget,
                       chapter_id=chapter_id)


def build_batches(
    concepts: list[dict],
    system_prompt: str,
    user_prompt_template: str,
    placeholder: str,
    model: str,
    max_output_tokens: int = 64000,
    ceiling: float = 0.95,
    tokens_per_output_item: int = 0,
) -> list[list[dict]]:
    """
    Build concept batches that fit within token limits.

    Uses token counting to ensure each batch stays under threshold.
    Batches concepts to minimize API calls while respecting token limits.

    Parameters:
    - tokens_per_output_item: if > 0, also limit batch size based on output capacity.
      output_limit = int((max_output_tokens * ceiling) / tokens_per_output_item).
      Batch closes when either input tokens exceed threshold OR batch size >= output_limit.
    """
    if not concepts:
        return []

    threshold = max_output_tokens * ceiling

    # Calculate output limit if specified
    output_limit = None
    if tokens_per_output_item > 0:
        output_limit = int((max_output_tokens * ceiling) / tokens_per_output_item)

    batches = []
    current_batch = []

    # Create router once outside loop — avoid repeated initialization
    _token_router = ProviderRouter(cfg=DEFAULT_CONFIG, stage="SURVEY")

    for concept in concepts:
        # Check output limit first (before token counting)
        if output_limit is not None and len(current_batch) >= output_limit:
            if current_batch:
                batches.append(current_batch)
            current_batch = [concept]
            continue

        # Try adding this concept to current batch
        tentative_batch = current_batch + [concept]
        batch_json = json.dumps(tentative_batch, indent=2)

        # Build full user prompt with this batch
        full_prompt = user_prompt_template.replace(placeholder, batch_json)

        # Count tokens for this batch
        try:
            input_tokens = _token_router.count_tokens(system_prompt, full_prompt)
        except Exception:
            # On error, just add concept and continue
            current_batch.append(concept)
            continue

        # Check if batch exceeds input threshold
        if input_tokens > threshold:
            if current_batch:
                batches.append(current_batch)
            current_batch = [concept]
        else:
            current_batch = tentative_batch

    # Add final batch
    if current_batch:
        batches.append(current_batch)

    return batches