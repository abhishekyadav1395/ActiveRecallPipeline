from __future__ import annotations

import asyncio
import dataclasses
import logging
import re
from pathlib import Path

from active_recall_pipeline.config import PipelineConfig, Exam, UPPSC_SUBJECTS, JAIIB_CAIIB_SUBJECTS
from active_recall_pipeline.pipeline import PipelineOrchestrator
from active_recall_pipeline.utils.db import SQLiteManager


logger = logging.getLogger(__name__)


class BatchScheduler:
    def __init__(self, cfg_template: PipelineConfig, db: SQLiteManager, max_concurrent: int = 3):
        self.cfg_template = cfg_template
        self.db = db
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.book_filter: str | None = None

    async def run(self) -> dict:
        """Discover PDFs, run all chapters concurrently, return summary."""
        pdfs = self._discover_pdfs()
        if not pdfs:
            logger.warning("No PDFs found in %s", self.cfg_template.raw_dir)
            return {"total": 0, "succeeded": 0, "failed": 0}

        print(f"[BATCH] Discovered {len(pdfs)} chapters")
        print(f"[BATCH] Starting concurrent processing (max {self.semaphore._value} simultaneous)")

        # Register all chapters in SQLite and prepare tasks
        tasks = []
        chapter_ids = []
        for metadata in pdfs:
            chapter_id = self.db.upsert_chapter(
                exam=metadata["exam"],
                subject=metadata["subject"],
                book=metadata["book"],
                chapter_num=metadata["chapter_num"],
                chapter_title=metadata["chapter_title"],
                pdf_path=str(metadata["pdf_path"]),
                input_mode=metadata["input_mode"],
            )
            self.db.init_stage_runs(chapter_id)
            cfg = self._build_chapter_config(metadata)
            tasks.append(self._run_chapter_async(chapter_id, cfg, metadata))
            chapter_ids.append(chapter_id)

        # Run all chapters concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Tally results and update chapter statuses
        succeeded = 0
        failed = 0
        for chapter_id, result in zip(chapter_ids, results):
            if isinstance(result, Exception):
                logger.error("Chapter %d raised exception: %s", chapter_id, result)
                self.db.set_chapter_status(chapter_id, "failed")
                failed += 1
            elif result:
                self.db.set_chapter_status(chapter_id, "completed")
                succeeded += 1
            else:
                self.db.set_chapter_status(chapter_id, "failed")
                failed += 1

        print(f"[BATCH] Complete: {succeeded}/{len(pdfs)} succeeded")
        return {"total": len(pdfs), "succeeded": succeeded, "failed": failed}

    async def _run_chapter_async(self, chapter_id: int, cfg: PipelineConfig, metadata: dict) -> bool:
        """Acquire semaphore, run chapter in executor, release."""
        display_name = metadata.get("chapter_title") or metadata["pdf_path"].stem
        async with self.semaphore:
            print(f"[BATCH] {display_name} started")
            loop = asyncio.get_event_loop()
            orchestrator = PipelineOrchestrator(cfg=cfg, db=self.db)
            try:
                result = await loop.run_in_executor(None, orchestrator.run_chapter, chapter_id)
                if result:
                    print(f"[BATCH] {display_name} completed [OK]")
                else:
                    print(f"[BATCH] {display_name} completed [FAIL]")
                return result
            except Exception as e:
                print(f"[BATCH] {display_name} failed with exception: {e}")
                raise

    def _discover_pdfs(self) -> list[dict]:
        """Scan raw_dir for PDFs. Return list of metadata dicts."""
        pdfs = []

        if not self.cfg_template.raw_dir.exists():
            logger.warning("raw_dir does not exist: %s", self.cfg_template.raw_dir)
            return pdfs

        # Look for full-book PDFs directly in raw_dir
        for pdf_path in self.cfg_template.raw_dir.glob("*.pdf"):
            metadata = self._parse_fullbook_pdf(pdf_path)
            if metadata:
                if self.book_filter and metadata["book"] != self.book_filter:
                    continue
                pdfs.append(metadata)

        # Look for chapter PDFs in subdirectories
        for subdir in self.cfg_template.raw_dir.iterdir():
            if not subdir.is_dir():
                continue

            for pdf_path in subdir.glob("*.pdf"):
                metadata = self._parse_chapter_pdf(pdf_path, subdir)
                if metadata:
                    if self.book_filter and metadata["book"] != self.book_filter:
                        continue
                    pdfs.append(metadata)

        return pdfs

    def _parse_fullbook_pdf(self, pdf_path: Path) -> dict | None:
        """Parse full-book PDF filename. Return metadata or None."""
        stem = pdf_path.stem
        # Expected format: {Subject}_{BookName}
        parts = stem.split("_", 1)
        if len(parts) != 2:
            logger.warning("Cannot parse full-book PDF filename: %s", pdf_path.name)
            return None

        subject, book = parts
        exam = self._detect_exam(subject)
        if not exam:
            logger.warning("Cannot detect exam from subject: %s in %s", subject, pdf_path.name)
            return None

        return {
            "pdf_path": pdf_path,
            "exam": exam.value,
            "subject": subject,
            "book": book,
            "chapter_num": None,
            "chapter_title": "",
            "input_mode": "full_book",
        }

    def _parse_chapter_pdf(self, pdf_path: Path, subdir: Path) -> dict | None:
        """Parse chapter PDF filename in subdirectory. Return metadata or None."""
        subdir_name = subdir.name
        # Expected subdir format: {Subject}_{BookName}
        parts = subdir_name.split("_", 1)
        if len(parts) != 2:
            logger.warning("Cannot parse subdirectory name: %s", subdir_name)
            return None

        subject, book = parts
        exam = self._detect_exam(subject)
        if not exam:
            logger.warning("Cannot detect exam from subject: %s in %s", subject, subdir_name)
            return None

        stem = pdf_path.stem
        # Expected filename format: Ch{NN}_{ChapterTitle}
        match = re.match(r"Ch(\d+)_(.*)", stem)
        if not match:
            logger.warning("Cannot parse chapter PDF filename: %s", pdf_path.name)
            return None

        chapter_num = int(match.group(1))
        chapter_title_camel = match.group(2)

        # Convert CamelCase to Title Case with spaces
        chapter_title = self._camel_to_title(chapter_title_camel)

        return {
            "pdf_path": pdf_path,
            "exam": exam.value,
            "subject": subject,
            "book": book,
            "chapter_num": chapter_num,
            "chapter_title": chapter_title,
            "input_mode": "manual_chapter",
        }

    def _detect_exam(self, subject: str) -> Exam | None:
        """Detect exam type from subject prefix."""
        if subject in UPPSC_SUBJECTS:
            return Exam.UPPSC
        elif subject in ["JAIIB", "CAIIB"]:
            return Exam.JAIIB_CAIIB
        else:
            return None

    def _camel_to_title(self, camel: str) -> str:
        """Convert CamelCase to Title Case with spaces."""
        # Insert space before uppercase letters (except first)
        result = re.sub(r"(?<!^)(?=[A-Z])", " ", camel)
        return result

    def _build_chapter_config(self, metadata: dict) -> PipelineConfig:
        """Clone cfg_template with chapter-specific overrides."""
        return dataclasses.replace(
            self.cfg_template,
            pdf_path=metadata["pdf_path"],
            exam=metadata["exam"],
            subject=metadata["subject"],
            book=metadata["book"],
            chapter_num=metadata["chapter_num"],
            chapter_title=metadata["chapter_title"],
            input_mode=metadata["input_mode"],
        )
