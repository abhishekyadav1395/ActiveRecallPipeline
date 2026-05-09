#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from active_recall_pipeline.config import PipelineConfig, Stage
from active_recall_pipeline.scheduler import BatchScheduler
from active_recall_pipeline.utils.db import SQLiteManager


logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Active Recall Pipeline — Batch processor (multi-chapter)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=3,
        help="Max chapters to process simultaneously (default: 3)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="INGEST",
        help="Starting stage (default: INGEST)",
    )
    parser.add_argument(
        "--stop",
        type=str,
        default="DELIVER",
        help="Stopping stage (default: DELIVER)",
    )
    parser.add_argument(
        "--skip",
        type=str,
        action="append",
        default=[],
        help="Stages to skip (can be repeated)",
    )
    parser.add_argument(
        "--book",
        type=str,
        default=None,
        help="Filter to one book (e.g. Polity_Laxmikant)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        return 1

    try:
        start_stage = Stage(args.start.upper())
        stop_stage = Stage(args.stop.upper())
        skip_stages = [Stage(s.upper()) for s in args.skip]
    except ValueError as e:
        print(f"ERROR: Invalid stage name: {e}", file=sys.stderr)
        return 1

    try:
        cfg = PipelineConfig(
            api_key=api_key,
            start_stage=start_stage,
            stop_stage=stop_stage,
            skip_stages=skip_stages,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    db = SQLiteManager()
    scheduler = BatchScheduler(
        cfg_template=cfg,
        db=db,
        max_concurrent=args.concurrent,
    )

    if args.book:
        scheduler.book_filter = args.book
        logger.info("Filtering to book: %s", args.book)

    summary = asyncio.run(scheduler.run())

    print(f"\nBatch complete: {summary['succeeded']}/{summary['total']} chapters succeeded")
    if summary["failed"] > 0:
        print(
            f"  {summary['failed']} chapters failed — "
            "run: python active_recall_pipeline/validate.py --fix"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
