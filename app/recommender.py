import random
from datetime import date, timedelta
from app.database import get_db


def get_todays_paper():
    """Get today's recommendation, creating one if needed."""
    db = get_db()
    today = date.today().isoformat()

    rec = db.execute(
        "SELECT dr.*, p.* FROM daily_recommendations dr "
        "JOIN papers p ON dr.paper_id = p.id "
        "WHERE dr.date = ? AND dr.status = 'shown'",
        (today,)
    ).fetchone()

    if rec:
        db.close()
        return dict(rec)

    paper = _select_paper(db)
    if not paper:
        db.close()
        return None

    db.execute(
        "INSERT INTO daily_recommendations (date, paper_id, status) VALUES (?, ?, 'shown')",
        (today, paper["id"])
    )
    db.commit()

    rec = db.execute(
        "SELECT dr.*, p.* FROM daily_recommendations dr "
        "JOIN papers p ON dr.paper_id = p.id "
        "WHERE dr.date = ? AND dr.status = 'shown'",
        (today,)
    ).fetchone()
    db.close()
    return dict(rec) if rec else None


def replace_todays_paper():
    """Replace today's paper with a new one."""
    db = get_db()
    today = date.today().isoformat()

    db.execute(
        "UPDATE daily_recommendations SET status = 'replaced' "
        "WHERE date = ? AND status = 'shown'",
        (today,)
    )

    paper = _select_paper(db)
    if not paper:
        db.close()
        return None

    db.execute(
        "INSERT INTO daily_recommendations (date, paper_id, status) VALUES (?, ?, 'shown')",
        (today, paper["id"])
    )
    db.commit()

    rec = db.execute(
        "SELECT dr.*, p.* FROM daily_recommendations dr "
        "JOIN papers p ON dr.paper_id = p.id "
        "WHERE dr.date = ? AND dr.status = 'shown'",
        (today,)
    ).fetchone()
    db.close()
    return dict(rec) if rec else None


def _select_paper(db):
    """Select a paper using weighted random draw with field diversity."""
    # Get papers already read/fully_noted
    exclude_ids = {
        row["paper_id"] for row in db.execute(
            "SELECT paper_id FROM user_papers WHERE status IN ('read', 'fully_noted')"
        ).fetchall()
    }

    # Get papers already shown today (including replaced)
    today_ids = {
        row["paper_id"] for row in db.execute(
            "SELECT paper_id FROM daily_recommendations WHERE date = ?",
            (date.today().isoformat(),)
        ).fetchall()
    }

    # Get recent fields for diversity
    recent_fields = [
        row["field"] for row in db.execute(
            "SELECT p.field FROM daily_recommendations dr "
            "JOIN papers p ON dr.paper_id = p.id "
            "WHERE dr.status = 'shown' "
            "ORDER BY dr.date DESC LIMIT 5"
        ).fetchall()
    ]

    # Pick type by weight: 40% classic, 30% modern, 20% working, 10% wildcard
    roll = random.random()
    if roll < 0.4:
        paper_type = "classic"
    elif roll < 0.7:
        paper_type = "modern"
    elif roll < 0.9:
        paper_type = "working"
    else:
        paper_type = None  # wildcard

    if paper_type:
        candidates = db.execute(
            "SELECT * FROM papers WHERE type = ?", (paper_type,)
        ).fetchall()
    else:
        candidates = db.execute("SELECT * FROM papers").fetchall()

    candidates = [dict(c) for c in candidates
                  if c["id"] not in exclude_ids and c["id"] not in today_ids]

    if not candidates:
        # Fallback: any paper not excluded
        candidates = [
            dict(c) for c in db.execute("SELECT * FROM papers").fetchall()
            if c["id"] not in exclude_ids and c["id"] not in today_ids
        ]

    if not candidates:
        return None

    # Apply field diversity: reduce weight for recently shown fields
    weighted = []
    for p in candidates:
        weight = 1.0
        count = recent_fields.count(p["field"])
        if count > 0:
            weight = max(0.1, 1.0 - (count * 0.3))
        weighted.append((p, weight))

    papers, weights = zip(*weighted)
    return random.choices(papers, weights=weights, k=1)[0]
