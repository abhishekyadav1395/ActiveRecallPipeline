from .ingest      import run as ingest
from .parse       import run as parse
from .survey      import run as survey
from .consolidate import run as consolidate
from .tier        import run as tier
from .excavate    import run as excavate
from .forge       import run as forge
from .audit       import run as audit
from .patch       import run as patch
from .mint        import run as mint
from .deliver     import run as deliver

from active_recall_pipeline.config import Stage

STAGE_RUNNERS = {
    Stage.INGEST:      ingest,
    Stage.PARSE:       parse,
    Stage.SURVEY:      survey,
    Stage.CONSOLIDATE: consolidate,
    Stage.TIER:        tier,
    Stage.EXCAVATE:    excavate,
    Stage.FORGE:       forge,
    Stage.AUDIT:       audit,
    Stage.PATCH:       patch,
    Stage.MINT:        mint,
    Stage.DELIVER:     deliver,
}

__all__ = ["STAGE_RUNNERS"]
