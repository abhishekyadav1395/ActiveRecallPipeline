# Graph Report - ActiveRecall  (2026-05-27)

## Corpus Check
- 38 files · ~24,375 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 603 nodes · 1183 edges · 44 communities (36 shown, 8 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 293 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c82a87f7`
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

## Communities (44 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (10): int, str, Validate and auto-coerce CONSOLIDATE output., Parse JSON from AI output. Strip ```json fences if present.         Returns (par, Parse JSON from AI output. Strip markdown fences if present., Return list of error strings for missing keys., Return list of error strings for missing keys., Validate and auto-coerce CONSOLIDATE output. (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (40): ABC, Provider, int, LLMResponse, str, int, str, int (+32 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (11): bool, Connection, Return True only if status=completed AND validation_status=passed.         Calle, Return True only if status=completed AND validation_status=passed.         Calle, Return True only if status=completed AND validation_status=passed., Return True only if status=completed AND validation_status=passed., Return True only if status=completed AND validation_status=passed.         Calle, Return stages where:         - status = pending or failed         - previous sta (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (53): bool, PipelineConfig, str, Exam, PipelineConfig, str, PipelineConfig, str (+45 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (39): AuditConfig, ConsolidateConfig, DeliverConfig, ExcavateConfig, ForgeConfig, IngestConfig, MintConfig, ParseConfig (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (37): Absolute Rules for This Session, Active Recall Pipeline, Alignment, check_input_file_exists function, Class: StageValidator, code:python (INTERIM = {), code:python (from dataclasses import dataclass, field), code:python (class StageValidator:) (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (44): PipelineConfig, PipelineConfig, str, PipelineConfig, float, PipelineConfig, bool, PipelineConfig (+36 more)

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
Cohesion: 0.19
Nodes (12): bool, int, str, Run one stage with retry logic. Return True if passed., Run one stage with retry logic. Return True if passed., Single execution attempt. Return True if stage + validation passed., Single execution attempt. Return True if stage + validation passed., Load chapter profile (CID) from interim file or database. (+4 more)

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
Cohesion: 0.23
Nodes (10): _ensure_dirs(), PipelineConfig, SQLiteManager, run(), Validate SCOUT output (Chapter Intelligence Document). Fatal on failure., Validate SURVEY output: list of section dicts., Validate SURVEY output: raw text string with numbered concept list., Validate SURVEY output. Only fails on unparseable structure. (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.20
Nodes (8): Build the context dict required by each validator., Build the context dict required by each validator., Build the context dict required by each validator., Build the context dict required by each validator., Load a JSON file from data/interim/. Return None if missing or invalid., Load a JSON file from data/interim/. Return None if missing or invalid., Load a JSON file from data/interim/. Return None if missing or invalid., Load a JSON file from data/interim/. Return None if missing or invalid.

### Community 28 - "Community 28"
Cohesion: 0.22
Nodes (6): int, Insert or replace chapter profile (CID) for a chapter., Return chapter profile (CID) for given chapter_id or None., Return total cost per provider for this chapter., Return total cost per provider for this chapter., Return total cost per provider for this chapter.

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (5): float, str, Upsert cost_ledger — add to totals if exists, insert if not., Upsert cost_ledger — add to totals if exists, insert if not., Upsert cost_ledger — add to totals if exists, insert if not.

### Community 30 - "Community 30"
Cohesion: 0.29
Nodes (5): Return chapter_id for given pdf_path or None., Return chapter_id for given pdf_path or None., Update chapter status and completed_at if status=completed., Return chapter_id for given pdf_path or None., Update chapter status and completed_at if status=completed.

### Community 31 - "Community 31"
Cohesion: 0.29
Nodes (5): Update stage status, timestamps, and error message., Update stage status, timestamps, and error message., Update validation status and errors (serialize as JSON)., Update stage status, timestamps, and error message., Update validation status and errors (serialize as JSON).

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (5): Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., Run the appropriate validator and write result to SQLite., ValidationResult

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (5): Validate TIER output: tiered concept inventory., Validate TIER output: list of section dicts., Validate TIER output: list of section dicts., Validate TIER output. Count/id mismatches are warnings only., Validate TIER output. Count/id mismatches are warnings only.

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (5): Validate EXCAVATE output: prerequisite chains., Validate EXCAVATE output: list of section dicts., Validate EXCAVATE output: list of section dicts., Validate EXCAVATE output. Missing concepts are warnings only., Validate EXCAVATE output. Missing concepts are warnings only.

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (5): Validate FORGE output: generated MCQ questions., Validate FORGE output. Auto-remove unusable questions. No floor check., Validate FORGE output: generated MCQ questions., Validate FORGE output: generated MCQ questions., Validate FORGE output. Auto-remove unusable questions. No floor check.

### Community 36 - "Community 36"
Cohesion: 0.33
Nodes (5): Validate PATCH output: merged forge + patch questions.         Only validates st, Validate PATCH output. Same philosophy as FORGE., Validate PATCH output: merged forge + patch questions.         Only validates st, Validate PATCH output: gap-fill questions., Validate PATCH output. Same philosophy as FORGE.

### Community 37 - "Community 37"
Cohesion: 0.50
Nodes (3): Return all chapters where status != completed and != failed., Return all chapters where status != completed and != failed., Return all chapters where status != completed and != failed.

### Community 38 - "Community 38"
Cohesion: 0.50
Nodes (3): Return all chapters regardless of status., Return all chapters regardless of status., Return all chapters regardless of status.

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (3): Insert a row for every stage with status=pending if not exists., Insert a row for every stage with status=pending if not exists., Insert a row for every stage with status=pending if not exists.

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (3): Return full stage_runs row as dict or None., Return full stage_runs row as dict or None., Return full stage_runs row as dict or None.

### Community 41 - "Community 41"
Cohesion: 0.50
Nodes (3): Increment retry_count and return new count., Increment retry_count and return new count., Increment retry_count and return new count.

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): Return total cost across all chapters all providers., Return total cost across all chapters all providers., Return total cost across all chapters all providers.

## Knowledge Gaps
- **47 isolated node(s):** `PreToolUse`, `allow`, `exam`, `subjects`, `survey_addition` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineConfig` connect `Community 7` to `Community 32`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 9`, `Community 10`, `Community 13`, `Community 26`?**
  _High betweenness centrality (0.296) - this node is a cross-community bridge._
- **Why does `SQLiteManager` connect `Community 7` to `Community 32`, `Community 2`, `Community 4`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 12`, `Community 10`, `Community 8`, `Community 26`, `Community 28`, `Community 29`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.221) - this node is a cross-community bridge._
- **Why does `Stage` connect `Community 4` to `Community 32`, `Community 2`, `Community 3`, `Community 6`, `Community 7`, `Community 9`, `Community 10`, `Community 26`, `Community 28`, `Community 29`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `PipelineConfig` (e.g. with `main()` and `main()`) actually correct?**
  _`PipelineConfig` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `SQLiteManager` (e.g. with `main()` and `main()`) actually correct?**
  _`SQLiteManager` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `LLMFatalError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMFatalError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `LLMBusyError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMBusyError` has 22 INFERRED edges - model-reasoned connections that need verification._