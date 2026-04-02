"""Insert missing seed papers into an existing database without touching user data."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, init_db


ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "seed_papers.json"


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def sync() -> None:
    init_db()
    db = get_db()

    papers = json.loads(SEED_PATH.read_text())
    existing = {
        normalize_title(row["title"])
        for row in db.execute("SELECT title FROM papers").fetchall()
    }

    inserted = 0
    for paper in papers:
        key = normalize_title(paper["title"])
        if key in existing:
            continue

        db.execute(
            """INSERT INTO papers (
                   title, authors, year, source, field, type, citation_proxy, url, summary_text
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                paper["title"],
                paper["authors"],
                paper.get("year"),
                paper.get("source", ""),
                paper.get("field", ""),
                paper.get("type", "modern"),
                paper.get("citation_proxy", 0),
                paper.get("url", ""),
                paper.get("summary_text"),
            ),
        )
        existing.add(key)
        inserted += 1

    db.commit()
    db.close()
    print(f"Inserted {inserted} missing papers.")


if __name__ == "__main__":
    sync()
