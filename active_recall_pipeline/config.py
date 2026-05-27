from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Stage registry
# ---------------------------------------------------------------------------

class Stage(str, Enum):
    INGEST      = "INGEST"
    PARSE       = "PARSE"
    SCOUT       = "SCOUT"
    SURVEY      = "SURVEY"
    CONSOLIDATE = "CONSOLIDATE"
    TIER        = "TIER"
    EXCAVATE    = "EXCAVATE"
    FORGE       = "FORGE"
    AUDIT       = "AUDIT"
    PATCH       = "PATCH"
    MINT        = "MINT"
    DELIVER     = "DELIVER"


STAGE_ORDER: list[Stage] = [
    Stage.INGEST,
    Stage.PARSE,
    Stage.SCOUT,
    Stage.SURVEY,
    Stage.CONSOLIDATE,
    Stage.TIER,
    Stage.EXCAVATE,
    Stage.FORGE,
    Stage.AUDIT,
    Stage.PATCH,
    Stage.MINT,
    Stage.DELIVER,
]


class Provider(str, Enum):
    ANTHROPIC_HAIKU  = "anthropic_haiku"
    ANTHROPIC_SONNET = "anthropic_sonnet"
    GEMINI_FLASH     = "gemini_flash"
    GEMINI_PRO       = "gemini_pro"
    DEEPSEEK_V3      = "deepseek_v3"
    DEEPSEEK_R1      = "deepseek_r1"


# Tier waterfall — ordered cheapest to most expensive
TIER_1_WATERFALL: list[Provider] = [
    Provider.DEEPSEEK_V3,
    Provider.GEMINI_FLASH,
    Provider.ANTHROPIC_HAIKU,
]

TIER_2_WATERFALL: list[Provider] = [
    Provider.DEEPSEEK_R1,
    Provider.GEMINI_PRO,
    Provider.ANTHROPIC_SONNET,
]

# Stage to tier mapping — override at runtime via CLI
STAGE_TIERS: dict[str, int] = {
    "INGEST":      0,
    "PARSE":       0,
    "SCOUT":       1,
    "SURVEY":      1,
    "CONSOLIDATE": 1,
    "TIER":        1,
    "EXCAVATE":    2,
    "FORGE":       1,
    "AUDIT":       0,
    "PATCH":       1,
    "MINT":        0,
    "DELIVER":     0,
}

# Provider pricing — USD per million tokens
PROVIDER_PRICING: dict[str, dict[str, float]] = {
    "anthropic_haiku":  {"input": 0.80,  "output": 4.00},
    "anthropic_sonnet": {"input": 3.00,  "output": 15.00},
    "gemini_flash":     {"input": 0.15,  "output": 0.60},
    "gemini_pro":       {"input": 1.25,  "output": 10.00},
    "deepseek_v3":      {"input": 0.27,  "output": 1.10},
    "deepseek_r1":      {"input": 0.55,  "output": 2.19},
}

# Retry and backoff settings
MAX_RETRIES_PER_PROVIDER: int = 3
BACKOFF_BASE_SECONDS: float = 2.0
BACKOFF_CAP_SECONDS: float = 60.0

# Cache TTL threshold — warm cache if silent for this many seconds
CACHE_WARM_THRESHOLD_SECONDS: float = 240.0


# ---------------------------------------------------------------------------
# Exams and subjects
# ---------------------------------------------------------------------------

class Exam(str, Enum):
    UPPSC = "uppsc"
    JAIIB_CAIIB = "jaiib_caiib"


EXAM_TO_PROFILE = {
    Exam.UPPSC: "profiles/uppsc_profile.json",
    Exam.JAIIB_CAIIB: "profiles/jaiib_caiib_profile.json",
}

UPPSC_SUBJECTS = [
    "Polity", "Modern History", "Ancient & Medieval History",
    "Geography", "Economy", "Environment", "S&T", "Art & Culture", "UP GK"
]

JAIIB_CAIIB_SUBJECTS = [
    "IE&FS", "PPB", "Accounting & Finance", "ABM",
    "BFM", "Retail Banking", "Risk Management"
]


# ---------------------------------------------------------------------------
# Path layout
# ---------------------------------------------------------------------------

ROOT_DIR       = Path(__file__).parent
DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
INTERIM_DIR    = DATA_DIR / "interim"
OUTPUT_DIR     = DATA_DIR / "output"
ARTIFACTS_DIR  = ROOT_DIR / "artifacts"
LOGS_DIR       = ROOT_DIR / "logs"
PROMPTS_DIR    = ROOT_DIR / "prompts"
PROFILES_DIR   = ROOT_DIR / "profiles"


# ---------------------------------------------------------------------------
# Per-stage config
# ---------------------------------------------------------------------------

@dataclass
class IngestConfig:
    """Extract metadata from PDF filenames. Model: Code only."""
    prefix_to_exam: dict[str, Exam] = field(default_factory=lambda: {
        "Polity": Exam.UPPSC,
        "JAIIB": Exam.JAIIB_CAIIB,
        "CAIIB": Exam.JAIIB_CAIIB,
    })


@dataclass
class ParseConfig:
    """Extract text and split into 10–15 page sections. Model: PyMuPDF."""
    section_page_count: int = 20
    overlap_pages: int = 1


@dataclass
class SurveyConfig:
    """Extract every surface concept from section text. Model: Claude Haiku."""
    model: str = "claude-3-5-haiku-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "survey_system.txt")


@dataclass
class ConsolidateConfig:
    """Transform raw SURVEY concepts into clean structured inventory. Model: Claude Haiku."""
    model: str = "claude-3-5-haiku-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "consolidate_system.txt")


@dataclass
class TierConfig:
    """Classify each concept: Simple/Medium/Complex. Model: Claude Haiku."""
    model: str = "claude-3-5-haiku-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "tier_system.txt")


@dataclass
class ExcavateConfig:
    """Build prerequisite chains per concept. Model: Claude Sonnet (with thinking)."""
    model: str = "claude-3-5-sonnet-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "excavate_system.txt")
    thinking_budget_simple: int = 0
    thinking_budget_medium: int = 2000
    thinking_budget_complex: int = 4000


@dataclass
class ForgeConfig:
    """Generate all MCQs across all 7 layers. Model: Claude Sonnet."""
    model: str = "claude-3-5-sonnet-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "forge_system.txt")


@dataclass
class AuditConfig:
    """Verify every inventory item has ≥1 question. Model: Code only."""
    pass


@dataclass
class PatchConfig:
    """Generate targeted questions for gaps. Model: Claude Sonnet."""
    model: str = "claude-3-5-sonnet-20241022"
    prompt_file: Path = field(default_factory=lambda: PROMPTS_DIR / "patch_system.txt")


@dataclass
class MintConfig:
    """Deduplicate + convert JSON to tilde CSV. Model: Code only."""
    pass


@dataclass
class DeliverConfig:
    """Write final CSV files per chapter and per book. Model: Code only."""
    csv_delimiter: str = "~"


# ---------------------------------------------------------------------------
# Top-level pipeline config
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    # Execution control
    start_stage: Stage = Stage.INGEST
    stop_stage:  Stage = Stage.DELIVER
    skip_stages: list[Stage] = field(default_factory=list)

    # Chapter metadata (populated from first PDF found or CLI args)
    exam: str = ""
    subject: str = ""
    book: str = ""
    chapter_num: int | None = None
    chapter_title: str = ""
    pdf_path: Path | None = None
    input_mode: str = ""

    # Runtime — populated by orchestrator before passing to stage runners
    db_logger: object = None  # SQLiteManager instance
    chapter_id: int | None = None

    # Paths (override per environment)
    root_dir:      Path = ROOT_DIR
    data_dir:      Path = DATA_DIR
    raw_dir:       Path = RAW_DIR
    interim_dir:   Path = INTERIM_DIR
    output_dir:    Path = OUTPUT_DIR
    artifacts_dir: Path = ARTIFACTS_DIR
    logs_dir:      Path = LOGS_DIR
    prompts_dir:   Path = PROMPTS_DIR
    profiles_dir:  Path = PROFILES_DIR

    # Logging
    log_level: str = "INFO"

    # API and model configuration
    api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )
    model_haiku: str = "claude-haiku-4-5-20251001"
    model_sonnet: str = "claude-sonnet-4-5"

    # Provider selection — set at runtime via CLI
    active_provider: str | None = None

    # API keys for additional providers
    gemini_api_key: str = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )
    deepseek_api_key: str = field(
        default_factory=lambda: os.environ.get("DEEPSEEK_API_KEY", "")
    )

    # Stage tier overrides — populated from CLI --stage-tier flags
    stage_tier_overrides: dict[str, int] = field(default_factory=dict)

    # SQLite database path
    db_path: Path = field(
        default_factory=lambda: DATA_DIR / "pipeline.db"
    )

    # Per-stage configs
    ingest:      IngestConfig      = field(default_factory=IngestConfig)
    parse:       ParseConfig       = field(default_factory=ParseConfig)
    survey:      SurveyConfig      = field(default_factory=SurveyConfig)
    consolidate: ConsolidateConfig = field(default_factory=ConsolidateConfig)
    tier:        TierConfig        = field(default_factory=TierConfig)
    excavate:    ExcavateConfig    = field(default_factory=ExcavateConfig)
    forge:       ForgeConfig       = field(default_factory=ForgeConfig)
    audit:       AuditConfig       = field(default_factory=AuditConfig)
    patch:       PatchConfig       = field(default_factory=PatchConfig)
    mint:        MintConfig        = field(default_factory=MintConfig)
    deliver:     DeliverConfig     = field(default_factory=DeliverConfig)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError(
                "api_key is required. Set via PipelineConfig(api_key='...') "
                "or environment variable ANTHROPIC_API_KEY"
            )

    def active_stages(self) -> list[Stage]:
        """Return ordered stages between start_stage and stop_stage, minus skips."""
        start = STAGE_ORDER.index(self.start_stage)
        stop  = STAGE_ORDER.index(self.stop_stage)
        return [
            s for s in STAGE_ORDER[start : stop + 1]
            if s not in self.skip_stages
        ]

    def stage_config(self, stage: Stage):
        return getattr(self, stage.value.lower())

    def get_stage_tier(self, stage: str) -> int:
        """Return tier for stage, respecting CLI overrides."""
        if stage in self.stage_tier_overrides:
            return self.stage_tier_overrides[stage]
        return STAGE_TIERS.get(stage, 0)

    def get_waterfall(self, tier: int) -> list[Provider]:
        """Return provider waterfall for given tier."""
        if self.active_provider:
            tier_waterfall = TIER_1_WATERFALL if tier == 1 else TIER_2_WATERFALL
            if self.active_provider == "anthropic":
                active = Provider("anthropic_haiku" if tier == 1 else "anthropic_sonnet")
            elif self.active_provider == "gemini":
                active = Provider("gemini_flash" if tier == 1 else "gemini_pro")
            elif self.active_provider == "deepseek":
                active = Provider("deepseek_v3" if tier == 1 else "deepseek_r1")
                return [active]  # DeepSeek only — no fallback to other providers
            else:
                active = Provider(self.active_provider + ("_v3" if tier == 1 else "_r1"))
            rest = [p for p in tier_waterfall if p != active]
            return [active] + rest
        return TIER_1_WATERFALL if tier == 1 else TIER_2_WATERFALL


DEFAULT_CONFIG = PipelineConfig()