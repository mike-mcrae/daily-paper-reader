from datetime import date, timedelta
from app.database import get_db


def update_streak():
    """Call this whenever a paper is marked read or fully_noted."""
    db = get_db()
    stats = db.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()
    today = date.today()

    if today.weekday() >= 5:
        db.close()
        return  # weekends don't count

    today_str = today.isoformat()
    last_active = stats["last_active_date"]

    if last_active == today_str:
        db.close()
        return  # already counted today

    current = stats["current_streak"]
    longest = stats["longest_streak"]

    if last_active:
        last_date = date.fromisoformat(last_active)
        # Find the previous weekday
        prev_weekday = today - timedelta(days=1)
        while prev_weekday.weekday() >= 5:
            prev_weekday -= timedelta(days=1)

        if last_date >= prev_weekday:
            current += 1
        else:
            current = 1
    else:
        current = 1

    longest = max(longest, current)

    # Count totals
    total_read = db.execute(
        "SELECT COUNT(*) FROM user_papers WHERE status = 'read'"
    ).fetchone()[0]
    total_noted = db.execute(
        "SELECT COUNT(*) FROM user_papers WHERE status = 'fully_noted'"
    ).fetchone()[0]

    db.execute(
        "UPDATE user_stats SET current_streak = ?, longest_streak = ?, "
        "total_read = ?, total_fully_noted = ?, last_active_date = ? WHERE id = 1",
        (current, longest, total_read, total_noted, today_str)
    )
    db.commit()
    db.close()
