"""Load seed papers from JSON into the database."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, init_db


def seed():
    init_db()
    db = get_db()

    existing = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    if existing > 0:
        print(f"Database already has {existing} papers. Skipping seed.")
        db.close()
        return

    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed_papers.json")
    with open(data_path) as f:
        papers = json.load(f)

    for p in papers:
        db.execute(
            """INSERT INTO papers (title, authors, year, source, field, type, citation_proxy, url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (p["title"], p["authors"], p.get("year"), p.get("source", ""),
             p.get("field", ""), p.get("type", "modern"),
             p.get("citation_proxy", 0), p.get("url", ""))
        )

    db.commit()
    print(f"Seeded {len(papers)} papers.")
    db.close()


if __name__ == "__main__":
    seed()
