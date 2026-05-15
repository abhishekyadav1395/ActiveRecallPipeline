# Graph Report - ActiveRecall  (2026-05-10)

## Corpus Check
- 33 files · ~56,065 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 406 nodes · 557 edges · 25 communities (20 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 89 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1e2bda08`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]

## God Nodes (most connected - your core abstractions)
1. `SQLiteManager` - 28 edges
2. `ProviderRouter` - 17 edges
3. `PipelineOrchestrator` - 16 edges
4. `BatchScheduler` - 15 edges
5. `LLMFatalError` - 14 edges
6. `AnthropicProvider` - 12 edges
7. `DeepSeekProvider` - 12 edges
8. `GeminiProvider` - 12 edges
9. `Deliverable 1 — utils/validation.py` - 12 edges
10. `main()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `Stage`  [INFERRED]
  run.py → active_recall_pipeline/config.py
- `main()` --calls--> `PipelineConfig`  [INFERRED]
  run.py → active_recall_pipeline/config.py
- `main()` --calls--> `SQLiteManager`  [INFERRED]
  run.py → active_recall_pipeline/utils/db.py
- `main()` --calls--> `PipelineOrchestrator`  [INFERRED]
  run.py → active_recall_pipeline/pipeline.py
- `main()` --calls--> `Stage`  [INFERRED]
  run_batch.py → active_recall_pipeline/config.py

## Communities (25 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (34): _ensure_dirs(), PipelineOrchestrator, Run one stage with retry logic. Return True if passed., Single execution attempt. Return True if stage + validation passed., Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Build the context dict required by each validator., Build the context dict required by each validator. (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (19): ABC, BaseProvider, Exception, AnthropicProvider, BaseProvider, LLMBusyError, LLMFatalError, LLMResponse (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (20): Insert or ignore chapter. Return chapter_id., Manages SQLite database operations for the pipeline., Return chapter_id for given pdf_path or None., Update chapter status and completed_at if status=completed., Initialize database manager and create tables if needed., Return all chapters where status != completed and != failed., Return all chapters regardless of status., Insert a row for every stage with status=pending if not exists. (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (28): _is_in_inventory(), _parse_batch_response(), EXCAVATE — Build prerequisite chains per concept using batching.      Input: con, Parse batch response from Sonnet (array of concept objects)., Parse batch response from Sonnet (array of concept objects)., Check if text already exists in concept inventory., Check if text already exists in concept inventory., run() (+20 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (27): AuditConfig, ConsolidateConfig, DeliverConfig, Exam, ExcavateConfig, ForgeConfig, IngestConfig, MintConfig (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (21): Absolute Rules for This Session, Active Recall Pipeline, Alignment, check_input_file_exists function, code:python (INTERIM = {), code:bash (python active_recall_pipeline/validate.py                  #), code:block7 (Active Recall Pipeline — Audit Report), code:python (def check_input_file_exists(stage: str, base_path: Path) -> ) (+13 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (16): AUDIT — Verify every inventory item has ≥1 question.      Input: config.interim_, run(), DELIVER — Write final CSV files per chapter and per book.      Input: config.int, Write questions to CSV with pipe delimiter., run(), _write_csv(), _jaccard_similarity(), MINT — Deduplicate questions using Jaccard similarity.      Input: config.interi (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (9): BatchScheduler, Parse full-book PDF filename. Return metadata or None., Parse chapter PDF filename in subdirectory. Return metadata or None., Detect exam type from subject prefix., Convert CamelCase to Title Case with spaces., Clone cfg_template with chapter-specific overrides., Discover PDFs, run all chapters concurrently, return summary., Acquire semaphore, run chapter in executor, release. (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (18): check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report(), print_full_report(), Print full audit report. Return 0 if all passed, 1 if failures found. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (12): PipelineConfig, Return ordered stages between start_stage and stop_stage, minus skips., Return ordered stages between start_stage and stop_stage, minus skips., Return tier for stage, respecting CLI overrides., Return ordered stages between start_stage and stop_stage, minus skips., Return provider waterfall for given tier., Return tier for stage, respecting CLI overrides., Return tier for stage, respecting CLI overrides. (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (16): main(), Main entry point for the pipeline., Main entry point for the pipeline., Main entry point for the pipeline., _detect_exam(), _extract_metadata_chapter(), _extract_metadata_full_book(), INGEST — Read PDF filenames, extract metadata.      Input: PDF files in cfg.raw_ (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (16): Class: StageValidator, code:python (from dataclasses import dataclass, field), code:python (class StageValidator:), code:block4 (concept_count < 20  → minimum 50 questions), code:python (def _parse_json_output(self, raw: str) -> tuple[list | dict ), Deliverable 1 — utils/validation.py, Error message style, Private helpers (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.23
Nodes (13): check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report(), print_full_report(), Print full audit report. Return 0 if all passed, 1 if failures found. (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.2
Nodes (13): _extract_chapters_from_toc(), _extract_pdf_text(), _extract_single_chapter(), Split chapter into sections of roughly 3000 words at paragraph boundaries., Split chapter into sections of roughly 3000 words at paragraph boundaries., PARSE — Extract text from PDFs and split into sections.      Input: config.inter, Extract chapters using table of contents., Extract entire PDF as single chapter. (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (12): Active Recall Pipeline — Session State, Actual File Tree (what exists right now), Architecture Decisions (do not revisit without updating this doc), code:block1 (ActiveRecall/), code:block2 (ActiveRecall/), Completed and Verified ✅, Current Build Position, Debt (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (10): _parse_and_validate_json(), Parse and validate JSON response from Haiku., Parse and validate JSON response from Haiku., Parse and validate JSON response from Haiku., CONSOLIDATE — Transform raw SURVEY concepts into clean structured inventory., Save raw response for debugging when parsing fails., Save raw response for debugging when parsing fails., Save raw response for debugging when parsing fails. (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (10): _load_profile(), _parse_forge_response(), FORGE — Generate all MCQs across all 7 layers.      Input: config.interim_dir/ex, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Parse forge response from Haiku., Parse forge response from Haiku., run() (+2 more)

## Knowledge Gaps
- **196 isolated node(s):** `Main entry point for the pipeline.`, `Main entry point for batch processing.`, `Return True if the input file for this stage exists and is non-zero.     interim`, `Return symbol and formatted status string.`, `Print detailed stage report for one chapter. Return (has_failures, failures_list` (+191 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProviderRouter` connect `Community 1` to `Community 9`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `SQLiteManager` connect `Community 2` to `Community 0`, `Community 4`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 12`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `PipelineConfig` connect `Community 9` to `Community 0`, `Community 1`, `Community 4`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `SQLiteManager` (e.g. with `PipelineOrchestrator` and `BatchScheduler`) actually correct?**
  _`SQLiteManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `str` (e.g. with `main()` and `print_full_report()`) actually correct?**
  _`str` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ProviderRouter` (e.g. with `Provider` and `PipelineConfig`) actually correct?**
  _`ProviderRouter` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `PipelineOrchestrator` (e.g. with `PipelineConfig` and `Stage`) actually correct?**
  _`PipelineOrchestrator` has 8 INFERRED edges - model-reasoned connections that need verification._