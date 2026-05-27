# Graph Report - ActiveRecall  (2026-05-27)

## Corpus Check
- 37 files · ~23,126 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 523 nodes · 1057 edges · 26 communities (19 shown, 7 thin omitted)
- Extraction: 73% EXTRACTED · 27% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `daa360c2`
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

## God Nodes (most connected - your core abstractions)
1. `PipelineConfig` - 76 edges
2. `SQLiteManager` - 47 edges
3. `LLMFatalError` - 33 edges
4. `LLMBusyError` - 29 edges
5. `Stage` - 28 edges
6. `Exam` - 28 edges
7. `PipelineOrchestrator` - 25 edges
8. `BaseProvider` - 25 edges
9. `ProviderRouter` - 22 edges
10. `LLMResponse` - 20 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `PipelineConfig`  [INFERRED]
  run.py → active_recall_pipeline/config.py
- `main()` --calls--> `_extract_metadata_full_book()`  [INFERRED]
  run.py → active_recall_pipeline/stages/ingest.py
- `main()` --calls--> `_extract_metadata_chapter()`  [INFERRED]
  run.py → active_recall_pipeline/stages/ingest.py
- `main()` --calls--> `PipelineConfig`  [INFERRED]
  run_batch.py → active_recall_pipeline/config.py
- `main()` --calls--> `SQLiteManager`  [INFERRED]
  validate.py → active_recall_pipeline/utils/db.py

## Communities (26 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (49): bool, int, PipelineConfig, SQLiteManager, str, Run one stage with retry logic. Return True if passed., Single execution attempt. Return True if stage + validation passed., Run the appropriate validator and write result to SQLite. (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (40): ABC, Provider, int, LLMResponse, str, int, str, int (+32 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): bool, float, int, str, Connection, Insert or ignore chapter. Return chapter_id., Return chapter_id for given pdf_path or None., Return chapter_id for given pdf_path or None. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (37): bool, PipelineConfig, str, Exam, int, PipelineConfig, str, float (+29 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (22): AuditConfig, ConsolidateConfig, DeliverConfig, ExcavateConfig, ForgeConfig, IngestConfig, MintConfig, ParseConfig (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (37): Absolute Rules for This Session, Active Recall Pipeline, Alignment, check_input_file_exists function, Class: StageValidator, code:python (INTERIM = {), code:python (from dataclasses import dataclass, field), code:python (class StageValidator:) (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (48): PipelineConfig, Return ordered stages between start_stage and stop_stage, minus skips., Return ordered stages between start_stage and stop_stage, minus skips., Return ordered stages between start_stage and stop_stage, minus skips., _ensure_dirs(), run(), PipelineConfig, PipelineConfig (+40 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (37): Exam, Stage, PipelineOrchestrator, BatchScheduler, bool, Exam, int, Path (+29 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (18): check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report(), print_full_report(), Print full audit report. Return 0 if all passed, 1 if failures found. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (7): int, Return tier for stage, respecting CLI overrides., Return provider waterfall for given tier., Return tier for stage, respecting CLI overrides., Return tier for stage, respecting CLI overrides., Return provider waterfall for given tier., Return provider waterfall for given tier.

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (19): Exam, Path, PipelineConfig, str, _detect_exam(), _extract_metadata_chapter(), _extract_metadata_full_book(), INGEST — Read PDF filenames, extract metadata.      Input: PDF files in cfg.raw_ (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (5): exam, forge_lineage, forge_matrix, subjects, survey_addition

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (24): PipelineConfig, str, check_input_file_exists(), do_fix(), format_stage_status(), main(), print_chapter_detail(), print_chapter_report() (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (16): int, PipelineConfig, str, _extract_chapters_from_toc(), _extract_pdf_text(), _extract_single_chapter(), Split chapter into sections of roughly 3000 words at paragraph boundaries., Split chapter into sections of roughly 3000 words at paragraph boundaries. (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (12): Active Recall Pipeline — Session State, Actual File Tree (what exists right now), Architecture Decisions (do not revisit without updating this doc), code:block1 (ActiveRecall/), code:block2 (ActiveRecall/), Completed and Verified ✅, Current Build Position, Debt (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (5): exam, forge_lineage, forge_matrix, subjects, survey_addition

## Knowledge Gaps
- **47 isolated node(s):** `PreToolUse`, `allow`, `exam`, `subjects`, `survey_addition` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineConfig` connect `Community 6` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 7`, `Community 9`, `Community 10`, `Community 12`, `Community 13`?**
  _High betweenness centrality (0.300) - this node is a cross-community bridge._
- **Why does `SQLiteManager` connect `Community 7` to `Community 0`, `Community 2`, `Community 6`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Why does `Stage` connect `Community 7` to `Community 0`, `Community 2`, `Community 4`, `Community 6`, `Community 12`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `PipelineConfig` (e.g. with `main()` and `main()`) actually correct?**
  _`PipelineConfig` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `SQLiteManager` (e.g. with `main()` and `main()`) actually correct?**
  _`SQLiteManager` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `LLMFatalError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMFatalError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `LLMBusyError` (e.g. with `AnthropicProvider` and `str`) actually correct?**
  _`LLMBusyError` has 22 INFERRED edges - model-reasoned connections that need verification._