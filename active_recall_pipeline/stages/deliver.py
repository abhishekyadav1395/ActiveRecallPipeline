from __future__ import annotations

import json
from collections import defaultdict

from active_recall_pipeline.config import PipelineConfig


def run(cfg: PipelineConfig) -> None:
    """
    DELIVER — Write final CSV files per chapter and per book.

    Input: config.interim_dir/minted_questions.json
    Output: CSV files in cfg.output_dir/
      - {subject}_{book}/Ch{num}_{title}.csv (per chapter)
      - {subject}_{book}_COMPLETE.csv (per book)
      - index.json (file listing)

    CSV delimiter: tilde (~)
    Columns: question ~ answer ~ tags

    Model: Code only
    """
    # Load questions
    questions_file = cfg.interim_dir / "minted_questions.json"
    with open(questions_file) as f:
        questions = json.load(f)

    # Group by chapter and book
    chapters = defaultdict(list)  # (subject, book, chapter_num, chapter_title) -> [questions]
    books = defaultdict(list)     # (subject, book) -> [questions]
    index = []

    for q in questions:
        chapter_key = (
            q.get("subject"),
            q.get("book"),
            q.get("chapter_num"),
            q.get("chapter_title"),
        )
        book_key = (q.get("subject"), q.get("book"))

        chapters[chapter_key].append(q)
        books[book_key].append(q)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # Write chapter files
    for (subject, book, chapter_num, chapter_title), chapter_qs in chapters.items():
        if not subject or not book:
            continue

        # Handle None chapter_num
        if chapter_num is None:
            chapter_num = 0
        clean_title = chapter_title.replace(" ", "") if chapter_title else "Unknown"

        # Create directory
        chapter_dir = cfg.output_dir / f"{subject}_{book}"
        chapter_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        filename = f"Ch{chapter_num:02d}_{clean_title}.csv"
        filepath = chapter_dir / filename

        # Write CSV
        _write_csv(filepath, chapter_qs)

        index.append({
            "type": "chapter",
            "subject": subject,
            "book": book,
            "chapter_num": chapter_num,
            "chapter_title": chapter_title,
            "filename": str(filepath.relative_to(cfg.output_dir)),
            "question_count": len(chapter_qs),
        })

    # Write book files
    for (subject, book), book_qs in books.items():
        if not subject or not book:
            continue

        filename = f"{subject}_{book}_COMPLETE.csv"
        filepath = cfg.output_dir / filename

        # Write CSV
        _write_csv(filepath, book_qs)

        index.append({
            "type": "book",
            "subject": subject,
            "book": book,
            "filename": str(filepath.relative_to(cfg.output_dir)),
            "question_count": len(book_qs),
        })

    # Write index
    index_file = cfg.output_dir / "index.json"
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)


def _write_csv(filepath, questions: list) -> None:
    """Write questions to CSV with pipe delimiter."""
    with open(filepath, "w", encoding="utf-8") as f:
        for q in questions:
            question_text = (q.get("question", "")
                             .replace("\n", "<br>")
                             .replace('"', '&quot;'))
            answer_text = (q.get("answer", "")
                           .replace("\n", "<br>")
                           .replace('"', '&quot;'))
            tags_text = q.get("tags", "")

            line = f'"{question_text}"|"{answer_text}"|"{tags_text}"\n'
            f.write(line)
