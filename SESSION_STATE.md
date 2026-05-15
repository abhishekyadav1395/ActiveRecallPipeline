# Active Recall Pipeline — Session State
Last Updated: 2026-05-08
Session Closed: Session 1

---

## Project Root
```
ActiveRecall/
├── run.py                          ← pipeline entry point
└── active_recall_pipeline/         ← all source code lives here
```
All Claude Code sessions must be opened from `ActiveRecall/` root.

---

## Current Build Position
- Phase: 1 (Core pipeline end to end)
- Next session task: Session 2 — Validation Layer
- Files to create:
  - `active_recall_pipeline/utils/validation.py`
  - `active_recall_pipeline/validate.py`

---

## Completed and Verified ✅

### Session 1 — SQLite Manager
- File: `active_recall_pipeline/utils/db.py`
- Class: `SQLiteManager`
- Status: Audited clean (external review, 2026-05-08)

**4 tables:**
- `chapters` — metadata and global pipeline status
- `stage_runs` — per-stage status + validation_status
- `api_calls` — granular API call log (tokens, cost, provider, duration)
- `cost_ledger` — aggregated costs per chapter/provider/tier

**15 methods:**
- Chapter: upsert_chapter, get_chapter_id, set_chapter_status, get_pending_chapters
- Stage: init_stage_runs, get_stage_status, set_stage_status, set_validation_status,
         stage_completed, increment_retry, get_actionable_stages
- API: log_api_call, update_cost_ledger
- Reporting: get_chapter_cost_summary, get_pipeline_summary

**Bug fixed before commit:**
- `get_actionable_stages` called `stage_completed()` while holding `self._lock`
- `threading.Lock()` is not reentrant — would deadlock under concurrency
- Fix: `_stage_completed_unsafe(conn, chapter_id, stage)` — no lock, takes open conn
- `stage_completed()` now delegates to `_unsafe` internally
- `get_actionable_stages` calls `_unsafe` directly with its own open connection

---

## Architecture Decisions (do not revisit without updating this doc)

| Decision | Rationale |
|---|---|
| `threading.Lock()` not `RLock` | `_unsafe` pattern is cleaner than reentrant lock |
| `INSERT OR IGNORE` in upsert_chapter | pdf_path is UNIQUE — safe idempotent insert |
| `ON CONFLICT DO UPDATE` in cost_ledger | Atomic upsert — no read-modify-write race |
| STAGE_ORDER from config drives init_stage_runs | Single source of truth for stage sequence |
| validation_status separate from status | Stage can be "completed but failed validation" |
| Flat interim file naming | All stage outputs in data/interim/ with fixed filenames — no subdirs |

---

## Actual File Tree (what exists right now)
```
ActiveRecall/
├── run.py
├── requirementV3.txt
├── SESSION_STATE.md                ← this file
├── SESSION_2_BUILD_PROMPT.md       ← paste into next Claude Code session
└── active_recall_pipeline/
    ├── __init__.py
    ├── config.py
    ├── pipeline.py
    ├── data/
    │   ├── raw/                    ← input PDFs go here
    │   ├── interim/                ← all stage JSON outputs (flat, fixed names)
    │   ├── output/
    │   │   └── index.json
    │   └── pipeline.db
    ├── stages/
    │   ├── __init__.py
    │   ├── ingest.py, parse.py, survey.py, consolidate.py, tier.py
    │   ├── excavate.py, forge.py, audit.py, patch.py, mint.py, deliver.py
    ├── prompts/
    │   ├── survey_system.txt, consolidate_system.txt, tier_system.txt
    │   ├── excavate_system.txt, forge_system.txt, patch_system.txt
    ├── profiles/
    │   ├── uppsc_profile.json
    │   └── jaiib_caiib_profile.json
    ├── models/__init__.py
    ├── utils/
    │   ├── __init__.py
    │   ├── api.py                  ← EXISTS, do not touch
    │   └── db.py                   ← Session 1 ✅
    ├── artifacts/
    └── logs/
```

---

## Interim File → Stage Mapping
| Stage | Reads | Writes |
|---|---|---|
| INGEST | data/raw/ PDFs | data/interim/ingest_metadata.json |
| PARSE | ingest_metadata.json | data/interim/parsed_sections.json |
| SURVEY | parsed_sections.json | data/interim/survey_concepts.json |
| CONSOLIDATE | survey_concepts.json | data/interim/consolidated_concepts.json |
| TIER | consolidated_concepts.json | data/interim/tiered_concepts.json |
| EXCAVATE | consolidated_concepts.json + tiered_concepts.json | data/interim/excavated_concepts.json |
| FORGE | excavated_concepts.json | data/interim/forge_questions.json |
| AUDIT | forge_questions.json | data/interim/audit_report.json + coverage_map.json |
| PATCH | audit_report.json | data/interim/patched_questions.json |
| MINT | forge_questions.json + patched_questions.json | data/interim/minted_questions.json |
| DELIVER | minted_questions.json | data/output/ |

---

## Stage Build Plan
| Session | What to Build | Status |
|---|---|---|
| Session 1 | `utils/db.py` — SQLiteManager | ✅ Done |
| Session 2 | `utils/validation.py` + `validate.py` CLI | ⬅ NEXT |
| Session 3 | `providers/` — BaseProvider, Anthropic, Gemini, DeepSeek, Router | Pending |
| Session 4 | `utils/api.py` — Cache Warmer + Router integration | Pending |
| Session 5 | Async Producer-Consumer scheduler | Pending |

---
## Debt 
- run.py imports _extract_metadata_full_book/_extract_metadata_chapter 
  from stages/ingest.py (private API) — fix when stages refactored
- Metadata extraction runs twice (run.py + INGEST stage) — acceptable for Phase 1
- _build_validation_context calls get_all_chapters() per stage — minor inefficiency