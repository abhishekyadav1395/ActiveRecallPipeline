# Graph Report - ActiveRecall  (2026-05-27)

## Corpus Check
- 38 files · ~24,471 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 607 nodes · 1187 edges · 51 communities (44 shown, 7 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 293 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4a6e1062`
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
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]

## God Nodes (most connected - your core abstractions)
1. `PipelineConfig` - 80 edges
2. `SQLiteManager` - 54 edges
3. `LLMFatalError` - 33 edges
4. `LLMBusyError` - 29 edges
5. `Stage` - 28 edges
6. `Exam` - 28 edges
7. `PipelineOrchestrator` - 27 edges
8. `BaseProvider` - 25 edges
9. `ProviderRouter` - 22 edges
10. `LLMResponse` - 20 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `Stage`  [INFERRED]
  run.py → active_recall_pipeline/config.py
- `main()` --calls--> `Stage`  [INFERRED]
  run_batch.py → active_recall_pipeline/config.py
- `str` --uses--> `SQLiteManager`  [INFERRED]
  validate.py → active_recall_pipeline/utils/db.py
- `Path` --uses--> `SQLiteManager`  [INFERRED]
  validate.py → active_recall_pipeline/utils/db.py
- `bool` --uses--> `SQLiteManager`  [INFERRED]
  validate.py → active_recall_pipeline/utils/db.py

## Communities (51 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (10): int, str, Validate and auto-coerce CONSOLIDATE output., Parse JSON from AI output. Strip ```json fences if present.         Returns (par, Parse JSON from AI output. Strip markdown fences if present., Return list of error strings for missing keys., Return list of error strings for missing keys., Validate and auto-coerce CONSOLIDATE output. (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (40): ABC, Provider, int, LLMResponse, str, int, str, int (+32 more)

### Community 2 - "Community 2"
Cohesion: 0.22
Nodes (8): bool, Connection, Return True only if status=completed AND validation_status=passed.         Calle, Return True only if status=completed AND validation_status=passed.         Calle, Return True only if status=completed AND validation_status=passed., Return True only if status=completed AND validation_status=passed., Return True only if status=completed AND validation_status=passed.         Calle, Return True only if status=completed AND validation_status=passed.

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (13): bool, PipelineConfig, str, _is_in_inventory(), _parse_batch_response(), EXCAVATE — Build prerequisite chains per concept using batching.      Input: con, Parse batch response from Sonnet (array of concept objects)., Parse batch response from Sonnet (array of concept objects). (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (36): AuditConfig, ConsolidateConfig, DeliverConfig, ExcavateConfig, ForgeConfig, IngestConfig, MintConfig, ParseConfig (+28 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (37): Absolute Rules for This Session, Active Recall Pipeline, Alignment, check_input_file_exists function, Class: StageValidator, code:python (INTERIM = {), code:python (from dataclasses import dataclass, field), code:python (class StageValidator:) (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (14): PipelineConfig, str, _parse_and_validate_json(), Parse and validate JSON response from Haiku., Parse and validate JSON response from Haiku., Parse and validate JSON response from Haiku., Parse and validate JSON response from Haiku., CONSOLIDATE — Transform raw SURVEY concepts into clean structured inventory. (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (58): Exam, PipelineConfig, PipelineOrchestrator, BatchScheduler, bool, Exam, int, Path (+50 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (18): check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report(), print_full_report(), Print full audit report. Return 0 if all passed, 1 if failures found. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (12): int, Return ordered stages between start_stage and stop_stage, minus skips., Return ordered stages between start_stage and stop_stage, minus skips., Return tier for stage, respecting CLI overrides., Return ordered stages between start_stage and stop_stage, minus skips., Return provider waterfall for given tier., Return tier for stage, respecting CLI overrides., Return tier for stage, respecting CLI overrides. (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (16): bool, int, str, Run one stage with retry logic. Return True if passed., Run one stage with retry logic. Return True if passed., Single execution attempt. Return True if stage + validation passed., Single execution attempt. Return True if stage + validation passed., Load a JSON file from data/interim/. Return None if missing or invalid. (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (5): exam, forge_lineage, forge_matrix, subjects, survey_addition

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (24): check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report(), print_full_report(), Print full audit report. Return 0 if all passed, 1 if failures found. (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (16): int, PipelineConfig, str, _extract_chapters_from_toc(), _extract_pdf_text(), _extract_single_chapter(), Split chapter into sections of roughly 3000 words at paragraph boundaries., Split chapter into sections of roughly 3000 words at paragraph boundaries. (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (12): Active Recall Pipeline — Session State, Actual File Tree (what exists right now), Architecture Decisions (do not revisit without updating this doc), code:block1 (ActiveRecall/), code:block2 (ActiveRecall/), Completed and Verified ✅, Current Build Position, Debt (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (5): exam, forge_lineage, forge_matrix, subjects, survey_addition

### Community 26 - "Community 26"
Cohesion: 0.26
Nodes (9): PipelineConfig, SQLiteManager, Validate SCOUT output (Chapter Intelligence Document). Fatal on failure., Validate SURVEY output: list of section dicts., Validate SURVEY output: raw text string with numbered concept list., Validate SURVEY output. Only fails on unparseable structure., StageValidator, ValidationResult (+1 more)

### Community 27 - "Community 27"
Cohesion: 0.20
Nodes (9): Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Build the context dict required by each validator., Build the context dict required by each validator., Build the context dict required by each validator., Build the context dict required by each validator. (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.22
Nodes (6): int, Insert a row for every stage with status=pending if not exists., Insert a row for every stage with status=pending if not exists., Insert or replace chapter profile (CID) for a chapter., Return chapter profile (CID) for given chapter_id or None., Insert a row for every stage with status=pending if not exists.

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (5): Update stage status, timestamps, and error message., Update stage status, timestamps, and error message., Update validation status and errors (serialize as JSON)., Update stage status, timestamps, and error message., Update validation status and errors (serialize as JSON).

### Community 30 - "Community 30"
Cohesion: 0.29
Nodes (5): Return chapter_id for given pdf_path or None., Return chapter_id for given pdf_path or None., Update chapter status and completed_at if status=completed., Return chapter_id for given pdf_path or None., Update chapter status and completed_at if status=completed.

### Community 31 - "Community 31"
Cohesion: 0.29
Nodes (7): int, PipelineConfig, str, _parse_tier_response(), Parse tier response from Haiku., TIER — Classify each concept: Simple/Medium/Complex.      Input: config.interim_, run()

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (19): Exam, PipelineConfig, str, _load_profile(), _parse_forge_response(), FORGE — Generate all MCQs across all 7 layers.      Input: config.interim_dir/ex, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out (+11 more)

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (5): Validate TIER output: tiered concept inventory., Validate TIER output: list of section dicts., Validate TIER output: list of section dicts., Validate TIER output. Count/id mismatches are warnings only., Validate TIER output. Count/id mismatches are warnings only.

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (5): Validate EXCAVATE output: prerequisite chains., Validate EXCAVATE output: list of section dicts., Validate EXCAVATE output: list of section dicts., Validate EXCAVATE output. Missing concepts are warnings only., Validate EXCAVATE output. Missing concepts are warnings only.

### Community 35 - "Community 35"
Cohesion: 0.21
Nodes (12): PipelineConfig, str, _parse_patch_response(), PATCH — Generate targeted questions for gaps identified by AUDIT.      Input: co, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Fix literal newlines and tabs inside JSON string values.     Haiku sometimes out, Parse patch response from Haiku. (+4 more)

### Community 36 - "Community 36"
Cohesion: 0.33
Nodes (5): Validate PATCH output: merged forge + patch questions.         Only validates st, Validate PATCH output. Same philosophy as FORGE., Validate PATCH output: merged forge + patch questions.         Only validates st, Validate PATCH output: gap-fill questions., Validate PATCH output. Same philosophy as FORGE.

### Community 37 - "Community 37"
Cohesion: 0.50
Nodes (3): Return all chapters regardless of status., Return all chapters regardless of status., Return all chapters regardless of status.

### Community 38 - "Community 38"
Cohesion: 0.24
Nodes (12): float, int, str, ProviderRouter, build_batches(), call_haiku(), call_sonnet(), get_router() (+4 more)

### Community 39 - "Community 39"
Cohesion: 0.28
Nodes (7): _ensure_dirs(), run(), PipelineConfig, DELIVER — Write final CSV files per chapter and per book.      Input: config.int, Write questions to CSV with pipe delimiter., run(), _write_csv()

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (3): Return full stage_runs row as dict or None., Return full stage_runs row as dict or None., Return full stage_runs row as dict or None.

### Community 41 - "Community 41"
Cohesion: 0.24
Nodes (9): bool, PipelineConfig, str, _is_valid_profile(), _parse_profile(), Check if profile has all required fields., SCOUT — Generate Chapter Intelligence Document (CID).      Input: config.interim, Parse JSON from SCOUT response. Handle markdown fences if present. (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (5): Path, Insert or ignore chapter. Return chapter_id., Insert or ignore chapter. Return chapter_id., Initialize database manager and create tables if needed., Create all tables if they don't exist.

### Community 43 - "Community 43"
Cohesion: 0.21
Nodes (9): PipelineConfig, float, PipelineConfig, AUDIT — Verify every inventory item has ≥1 question.      Input: config.interim_, run(), _jaccard_similarity(), MINT — Deduplicate questions using Jaccard similarity.      Input: config.interi, Calculate Jaccard similarity between two sets. (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.33
Nodes (5): float, str, Upsert cost_ledger — add to totals if exists, insert if not., Upsert cost_ledger — add to totals if exists, insert if not., Upsert cost_ledger — add to totals if exists, insert if not.

### Community 45 - "Community 45"
Cohesion: 0.33
Nodes (5): Validate FORGE output: generated MCQ questions., Validate FORGE output. Auto-remove unusable questions. No floor check., Validate FORGE output: generated MCQ questions., Validate FORGE output: generated MCQ questions., Validate FORGE output. Auto-remove unusable questions. No floor check.

### Community 46 - "Community 46"
Cohesion: 0.50
Nodes (3): Return all chapters where status != completed and != failed., Return all chapters where status != completed and != failed., Return all chapters where status != completed and != failed.

### Community 47 - "Community 47"
Cohesion: 0.50
Nodes (3): Increment retry_count and return new count., Increment retry_count and return new count., Increment retry_count and return new count.

### Community 48 - "Community 48"
Cohesion: 0.50
Nodes (3): Return stages where:         - status = pending or failed         - previous sta, Return stages where:         - status = pending or failed         - previous sta, Return stages where:         - status = pending or failed         - previous sta

### Community 49 - "Community 49"
Cohesion: 0.50
Nodes (3): Return total cost per provider for this chapter., Return total cost per provider for this chapter., Return total cost per provider for this chapter.

### Community 50 - "Community 50"
Cohesion: 0.50
Nodes (3): Return total cost across all chapters all providers., Return total cost across all chapters all providers., Return total cost across all chapters all providers.

## Knowledge Gaps
- **47 isolated node(s):** `PreToolUse`, `allow`, `exam`, `subjects`, `survey_addition` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineConfig` connect `Community 7` to `Community 32`, `Community 1`, `Community 3`, `Community 4`, `Community 35`, `Community 6`, `Community 39`, `Community 9`, `Community 41`, `Community 43`, `Community 10`, `Community 13`, `Community 26`, `Community 27`, `Community 31`?**
  _High betweenness centrality (0.297) - this node is a cross-community bridge._
- **Why does `SQLiteManager` connect `Community 7` to `Community 2`, `Community 4`, `Community 8`, `Community 10`, `Community 12`, `Community 26`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 37`, `Community 39`, `Community 40`, `Community 42`, `Community 44`, `Community 46`, `Community 47`, `Community 48`, `Community 49`, `Community 50`?**
  _High betweenness centrality (0.220) - this node is a cross-community bridge._
- **Why does `Stage` connect `Community 4` to `Community 2`, `Community 39`, `Community 7`, `Community 9`, `Community 10`, `Community 43`, `Community 42`, `Community 44`, `Community 26`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `PipelineConfig` (e.g. with `main()` and `main()`) actually correct?**
  _`PipelineConfig` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `SQLiteManager` (e.g. with `main()` and `main()`) actually correct?**
  _`SQLiteManager` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `LLMFatalError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMFatalError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `LLMBusyError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMBusyError` has 22 INFERRED edges - model-reasoned connections that need verification._