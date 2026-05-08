# Session 2 Build Prompt — Validation Layer
# Active Recall Pipeline
# Paste this into Claude Code after the opening prompt

---

## Context

You have read config.py and utils/db.py.
Session 1 (SQLiteManager) is complete and audited. Do not touch db.py.
utils/api.py already exists. Do not touch it.

---

## Session 2 Task

Build the Validation Layer. Two deliverables only:

1. `active_recall_pipeline/utils/validation.py` — inline validators for every AI stage
2. `active_recall_pipeline/validate.py` — standalone CLI audit tool

Do not create any other files.
Do not modify any existing files.

---

## Interim File Paths (use these exact paths)

All stage outputs live flat in `active_recall_pipeline/data/interim/`:

```python
INTERIM = {
    "INGEST":      "active_recall_pipeline/data/interim/ingest_metadata.json",
    "PARSE":       "active_recall_pipeline/data/interim/parsed_sections.json",
    "SURVEY":      "active_recall_pipeline/data/interim/survey_concepts.json",
    "CONSOLIDATE": "active_recall_pipeline/data/interim/consolidated_concepts.json",
    "TIER":        "active_recall_pipeline/data/interim/tiered_concepts.json",
    "EXCAVATE":    "active_recall_pipeline/data/interim/excavated_concepts.json",
    "FORGE":       "active_recall_pipeline/data/interim/forge_questions.json",
    "AUDIT":       "active_recall_pipeline/data/interim/audit_report.json",
    "COVERAGE":    "active_recall_pipeline/data/interim/coverage_map.json",
    "PATCH":       "active_recall_pipeline/data/interim/patched_questions.json",
    "MINT":        "active_recall_pipeline/data/interim/minted_questions.json",
}
```

Each stage validator checks that its input file exists and is non-zero
before validating the content. Input file for each stage is the
previous stage's output file per the mapping above.

---

## Deliverable 1 — utils/validation.py

### Purpose
Pure Python. No API calls. No external dependencies beyond stdlib.
Called inline after every AI stage completes.
Returns structured results that db.py writes to stage_runs.

### ValidationResult dataclass

```python
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)    # blocking — triggers retry
    warnings: list[str] = field(default_factory=list)  # non-blocking — logged only
```

### Class: StageValidator

Single class. One public method per AI stage.

```python
class StageValidator:
    def validate_survey(self, output: str, context: dict) -> ValidationResult
    def validate_consolidate(self, output: list, context: dict) -> ValidationResult
    def validate_tier(self, output: list, context: dict) -> ValidationResult
    def validate_excavate(self, output: list, context: dict) -> ValidationResult
    def validate_forge(self, output: list, context: dict) -> ValidationResult
    def validate_patch(self, output: list, context: dict) -> ValidationResult
```

`output` is already parsed (caller parses JSON before calling validator).
`context` carries what the validator needs from upstream — see per-stage spec below.

---

### validate_survey(output: str, context: dict) -> ValidationResult

`output` — raw text string from SURVEY (numbered concept list)

Checks (all blocking errors unless marked warning):
- output is a non-empty string
- contains at least 10 lines matching `^\d+\.` (numbered items)
- no single line exceeds 300 characters
- does not contain markdown headers (lines starting with `#`)
- does not contain the chapter title verbatim
  (context key: `chapter_title: str`)

---

### validate_consolidate(output: list, context: dict) -> ValidationResult

`output` — parsed JSON array from CONSOLIDATE

Checks:
- output is a non-empty list
- every item has all four keys: `id`, `text`, `type`, `children`
- every `item.type` is exactly `"STANDALONE"` or `"CLUSTER"`
- every `item.id` is an integer
- all ids are unique
- ids are sequential starting from 1
  (warning not error if out of sequence — model sometimes skips)
- STANDALONE items: `children == []`
- CLUSTER items: `len(children) >= 3`
  (items with 1-2 children are an error — spec requires STANDALONE for < 3)
- no `item.text` is empty string or whitespace only

---

### validate_tier(output: list, context: dict) -> ValidationResult

`output` — parsed JSON array from TIER

Context keys:
- `consolidate_count: int` — number of items in consolidate output
- `consolidate_ids: list[int]` — all ids from consolidate output

Checks:
- output is a non-empty list
- every item has keys: `id`, `tier`
- every `item.tier` is exactly `"SIMPLE"`, `"MEDIUM"`, or `"COMPLEX"`
- count of items matches `consolidate_count`
- every id from `consolidate_ids` appears in tier output
  (missing ids listed individually in error message)

---

### validate_excavate(output: list, context: dict) -> ValidationResult

`output` — parsed JSON array from EXCAVATE

Context keys:
- `non_simple_ids: list[int]` — ids of MEDIUM + COMPLEX concepts from TIER

Checks:
- output is a non-empty list
- every item has keys: `concept_id`, `concept_text`, `prerequisites`
- `prerequisites` is a list (empty list is valid for edge cases)
- every prerequisite has keys: `depth`, `text`, `reason`
- every `prerequisite.depth` is a positive integer >= 1
- prerequisites within each concept are ordered depth descending
  (warning, not error — model sometimes slightly misordered)
- every id in `non_simple_ids` appears in output as `concept_id`
  (missing ids listed individually)

---

### validate_forge(output: list, context: dict) -> ValidationResult

`output` — parsed JSON array from FORGE

Context keys:
- `concept_count: int` — number of concepts in consolidated inventory

Minimum question floor (blocking error if not met):
```
concept_count < 20  → minimum 50 questions
concept_count 20-40 → minimum 75 questions
concept_count 40-60 → minimum 100 questions
concept_count > 60  → minimum 120 questions
```

Checks:
- output is a non-empty list
- length meets minimum floor for concept_count
- every item has keys: `q_id`, `inventory_id`, `layer`, `format`,
  `difficulty`, `question`, `answer`, `tags`
- `layer` is one of: Foundation, Surface, Reasoning, Boundary,
  Ordering, Matrix, Lineage
- `format` is one of: Direct, Statement, Ordering
- `difficulty` is one of: Easy, Medium, Hard
- all `q_id` values are unique (list duplicates found)
- `question` field is non-empty string
- `answer` field is non-empty string
- `tags` field contains substring `"Inventory::"`

---

### validate_patch(output: list, context: dict) -> ValidationResult

`output` — parsed JSON array from PATCH

Context keys:
- `gap_ids: set[int]` — inventory ids that had no coverage (from AUDIT)
- `existing_q_ids: set[str]` — q_ids already in forge batch

Checks:
- output is a non-empty list
- every item has same required keys as forge output
- every item has `"GapFill::true"` in tags field
- every `inventory_id` in output exists in `gap_ids`
  (PATCH must only fill gaps — extra ids are an error)
- no `q_id` duplicates within patch output
- no `q_id` already exists in `existing_q_ids`

---

### Private helpers

```python
def _parse_json_output(self, raw: str) -> tuple[list | dict | None, str | None]:
    """Parse JSON from AI output. Strip ```json fences if present.
    Returns (parsed_object, None) on success.
    Returns (None, error_message) on failure.
    """

def _check_required_keys(self, item: dict, required: set[str], item_index: int) -> list[str]:
    """Return list of error strings for missing keys.
    Format: "Item {item_index}: missing key '{key}'"
    """
```

### Error message style
- Specific: `"Item 3: missing key 'children'"` not `"Invalid item"`
- Include counts: `"Only 8 numbered lines found, minimum is 10"`
- Include offending value: `"Item 5: type='CLUSTER' has 2 children, minimum is 3"`
- List all failures, not just first: never stop at first error

---

## Deliverable 2 — validate.py (CLI tool)

### Location
`active_recall_pipeline/validate.py`
(sits alongside pipeline.py and config.py, not inside utils/)

### Usage
```bash
python active_recall_pipeline/validate.py                  # full audit
python active_recall_pipeline/validate.py --chapter 3      # one chapter
python active_recall_pipeline/validate.py --fix            # reset failed → pending
python active_recall_pipeline/validate.py --chapter 3 --fix
```

### Implementation rules
- `argparse` for CLI args
- Import `SQLiteManager` from `active_recall_pipeline.utils.db`
- Import `STAGE_ORDER` from `active_recall_pipeline.config`
- stdlib only — no rich, no click, no tabulate
- `Path` from pathlib for all file existence checks

### Full audit output format
```
Active Recall Pipeline — Audit Report
======================================
Chapters: 3 total | 1 completed | 2 in progress | 0 failed

Chapter 1: Polity_Laxmikant / Ch01_HistoricalUnderpinnings
  INGEST      ✅ completed  | validation: passed
  PARSE       ✅ completed  | validation: passed
  SURVEY      ✅ completed  | validation: passed
  CONSOLIDATE ✅ completed  | validation: passed
  TIER        ✅ completed  | validation: passed
  EXCAVATE    ✅ completed  | validation: passed
  FORGE       ❌ failed     | validation: failed | retries: 2/3
               Errors: Only 43 questions generated, minimum is 75
  AUDIT       ⏸ pending
  PATCH       ⏸ pending
  MINT        ⏸ pending
  DELIVER     ⏸ pending

======================================
Cost Summary
  anthropic  : $0.0312  (45,230 in / 12,100 out tokens)
  deepseek   : $0.0021  (18,900 in / 6,200 out tokens)
  TOTAL      : $0.0333

Interim files present:
  ✅ ingest_metadata.json
  ✅ parsed_sections.json
  ✅ survey_concepts.json
  ✅ consolidated_concepts.json
  ✅ tiered_concepts.json
  ✅ excavated_concepts.json
  ❌ forge_questions.json (missing)
```

### Status symbols
- ✅ completed
- ❌ failed
- 🔄 running
- ⏸ pending
- ⚠️ completed but validation pending/failed

### Alignment
Use `str.ljust()` to align stage name column to 12 chars.

### --fix behaviour
- Find all `stage_runs` where `status = 'failed'`
- Reset: `status = 'pending'`, clear `error_message`, clear `validation_errors`
- Do NOT reset `retry_count`
- Print each reset: `"  Reset: Chapter 1 / FORGE → pending"`
- Print total count at end

### check_input_file_exists function
Implement as standalone function (not method) in validate.py:

```python
def check_input_file_exists(stage: str, base_path: Path) -> bool:
    """Return True if the input file for this stage exists and is non-zero."""
```

Use the INTERIM mapping at the top of this prompt for file paths.
`base_path` is the project root (parent of active_recall_pipeline/).

### Exit codes
- `sys.exit(0)` — all stages passed or no failures found
- `sys.exit(1)` — any stage has status=failed or validation=failed

---

## Absolute Rules for This Session

1. Pure Python only — no API calls in validation.py or validate.py
2. No new pip dependencies — stdlib only
3. All `ValidationResult.errors` are plain strings — never nested objects
4. Do not modify db.py, config.py, api.py, or any existing file
5. Do not create test files — tests come in a later session
6. Interim file paths must match the exact filenames in the mapping above
7. If a validator check requires context not available at call time,
   add a warning (not blocking error) and note it in a comment
