import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date

from app.database import get_db, init_db
from app.recommender import get_todays_paper, replace_todays_paper
from app.streaks import update_streak

ROOT_PATH = os.getenv("ROOT_PATH", "")
app = FastAPI(title="Daily Economics Paper Reader")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["base"] = ROOT_PATH


def default_redirect_path() -> str:
    return f"{ROOT_PATH}/" if ROOT_PATH else "/"


def resolve_redirect_path(next_path: str | None) -> str:
    if next_path and next_path.startswith("/"):
        return next_path
    return default_redirect_path()


def ensure_user_paper_entry(db, paper_id: int, status: str = "saved") -> None:
    existing = db.execute(
        "SELECT id FROM user_papers WHERE paper_id = ?",
        (paper_id,),
    ).fetchone()
    if not existing:
        db.execute(
            "INSERT INTO user_papers (paper_id, status) VALUES (?, ?)",
            (paper_id, status),
        )


@app.on_event("startup")
def startup():
    init_db()


# ── Today Page ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def today_page(request: Request):
    paper = get_todays_paper()
    db = get_db()
    status = None
    if paper:
        row = db.execute(
            "SELECT status FROM user_papers WHERE paper_id = ?", (paper["id"],)
        ).fetchone()
        if row:
            status = row["status"]
    stats = db.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()
    db.close()
    return templates.TemplateResponse(request, "today.html", {
        "paper": paper,
        "status": status,
        "stats": dict(stats) if stats else {},
        "today": date.today().strftime("%A, %B %d, %Y"),
    })


@app.post("/replace")
def replace_paper():
    replace_todays_paper()
    return RedirectResponse(default_redirect_path(), status_code=303)


@app.post("/status/{paper_id}")
def set_status(
    paper_id: int,
    status: str = Form(...),
    next_path: str | None = Form(None),
):
    db = get_db()
    existing = db.execute(
        "SELECT id FROM user_papers WHERE paper_id = ?", (paper_id,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE user_papers SET status = ?, last_updated = datetime('now') WHERE paper_id = ?",
            (status, paper_id)
        )
    else:
        db.execute(
            "INSERT INTO user_papers (paper_id, status) VALUES (?, ?)",
            (paper_id, status)
        )
    db.commit()
    db.close()

    if status in ("read", "fully_noted"):
        update_streak()

    return RedirectResponse(resolve_redirect_path(next_path), status_code=303)


# ── Explore Page ────────────────────────────────────────────

@app.get("/explore", response_class=HTMLResponse)
def explore_page(
    request: Request,
    q: str = "",
    field: str = "",
    paper_type: str = "",
    source: str = "",
    status: str = "",
    page: int = 1,
):
    db = get_db()
    per_page = 20
    conditions = []
    params = []

    if q:
        conditions.append("(p.title LIKE ? OR p.authors LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if field:
        conditions.append("p.field = ?")
        params.append(field)
    if paper_type:
        conditions.append("p.type = ?")
        params.append(paper_type)
    if source:
        conditions.append("p.source = ?")
        params.append(source)
    if status:
        conditions.append("up.status = ?")
        params.append(status)

    where = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT p.*, up.status as user_status
        FROM papers p
        LEFT JOIN user_papers up ON p.id = up.paper_id
        WHERE {where}
        ORDER BY p.year DESC, p.title
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, (page - 1) * per_page])
    papers = [dict(r) for r in db.execute(query, params).fetchall()]

    count_params = params[:-2]
    total = db.execute(
        f"SELECT COUNT(*) FROM papers p LEFT JOIN user_papers up ON p.id = up.paper_id WHERE {where}",
        count_params
    ).fetchone()[0]

    # Get filter options
    fields = [r[0] for r in db.execute("SELECT DISTINCT field FROM papers ORDER BY field").fetchall()]
    sources = [r[0] for r in db.execute("SELECT DISTINCT source FROM papers ORDER BY source").fetchall()]

    db.close()
    return templates.TemplateResponse(request, "explore.html", {
        "papers": papers,
        "fields": fields,
        "sources": sources,
        "q": q,
        "field": field,
        "paper_type": paper_type,
        "source": source,
        "status": status,
        "page": page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    })


# ── Library Page ────────────────────────────────────────────

@app.get("/library", response_class=HTMLResponse)
def library_page(request: Request, tab: str = "saved"):
    db = get_db()
    status_map = {
        "saved": ("saved",),
        "started": ("started",),
        "completed": ("read", "fully_noted"),
        "skipped": ("skipped",),
    }
    statuses = status_map.get(tab, ("saved",))
    placeholders = ",".join("?" for _ in statuses)

    papers = [dict(r) for r in db.execute(
        f"""SELECT p.*, up.status as user_status, up.last_updated
            FROM papers p JOIN user_papers up ON p.id = up.paper_id
            WHERE up.status IN ({placeholders})
            ORDER BY up.last_updated DESC""",
        statuses
    ).fetchall()]

    counts = {}
    for key, vals in status_map.items():
        ph = ",".join("?" for _ in vals)
        counts[key] = db.execute(
            f"SELECT COUNT(*) FROM user_papers WHERE status IN ({ph})", vals
        ).fetchone()[0]

    db.close()
    return templates.TemplateResponse(request, "library.html", {
        "papers": papers,
        "tab": tab,
        "counts": counts,
    })


# ── Notes Page ──────────────────────────────────────────────

@app.get("/notes/{paper_id}", response_class=HTMLResponse)
def notes_page(request: Request, paper_id: int):
    db = get_db()
    paper = db.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    notes = db.execute("SELECT * FROM notes WHERE paper_id = ?", (paper_id,)).fetchone()
    user_paper = db.execute(
        "SELECT status FROM user_papers WHERE paper_id = ?",
        (paper_id,),
    ).fetchone()
    db.close()
    return templates.TemplateResponse(request, "notes.html", {
        "paper": dict(paper) if paper else None,
        "notes": dict(notes) if notes else None,
        "status": user_paper["status"] if user_paper else None,
    })


@app.post("/notes/{paper_id}")
def save_notes(
    paper_id: int,
    summary: str = Form(""),
    key_findings: str = Form(""),
    contribution: str = Form(""),
    methodology: str = Form(""),
    assumptions_stated: str = Form(""),
    assumptions_unstated: str = Form(""),
    improvements: str = Form(""),
    quotes: str = Form(""),
):
    db = get_db()
    ensure_user_paper_entry(db, paper_id)
    existing = db.execute("SELECT id FROM notes WHERE paper_id = ?", (paper_id,)).fetchone()
    if existing:
        db.execute(
            """UPDATE notes SET summary=?, key_findings=?, contribution=?,
               methodology=?, assumptions_stated=?, assumptions_unstated=?,
               improvements=?, quotes=?, updated_at=datetime('now')
               WHERE paper_id=?""",
            (summary, key_findings, contribution, methodology,
             assumptions_stated, assumptions_unstated, improvements, quotes, paper_id)
        )
    else:
        db.execute(
            """INSERT INTO notes (paper_id, summary, key_findings, contribution,
               methodology, assumptions_stated, assumptions_unstated, improvements, quotes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paper_id, summary, key_findings, contribution, methodology,
             assumptions_stated, assumptions_unstated, improvements, quotes)
        )
    db.commit()
    db.close()
    return RedirectResponse(f"{ROOT_PATH}/notes/{paper_id}", status_code=303)


@app.post("/api/notes/{paper_id}")
def autosave_notes(
    paper_id: int,
    summary: str = Form(""),
    key_findings: str = Form(""),
    contribution: str = Form(""),
    methodology: str = Form(""),
    assumptions_stated: str = Form(""),
    assumptions_unstated: str = Form(""),
    improvements: str = Form(""),
    quotes: str = Form(""),
):
    db = get_db()
    ensure_user_paper_entry(db, paper_id)
    existing = db.execute("SELECT id FROM notes WHERE paper_id = ?", (paper_id,)).fetchone()
    if existing:
        db.execute(
            """UPDATE notes SET summary=?, key_findings=?, contribution=?,
               methodology=?, assumptions_stated=?, assumptions_unstated=?,
               improvements=?, quotes=?, updated_at=datetime('now')
               WHERE paper_id=?""",
            (summary, key_findings, contribution, methodology,
             assumptions_stated, assumptions_unstated, improvements, quotes, paper_id)
        )
    else:
        db.execute(
            """INSERT INTO notes (paper_id, summary, key_findings, contribution,
               methodology, assumptions_stated, assumptions_unstated, improvements, quotes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paper_id, summary, key_findings, contribution, methodology,
             assumptions_stated, assumptions_unstated, improvements, quotes)
        )
    db.commit()
    db.close()
    return {"ok": True}


# ── Stats Page ──────────────────────────────────────────────

@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    db = get_db()
    stats = db.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()

    # Weekly progress: papers read/noted in last 7 days
    weekly = db.execute(
        """SELECT COUNT(*) FROM user_papers
           WHERE status IN ('read', 'fully_noted')
           AND last_updated >= date('now', '-7 days')"""
    ).fetchone()[0]

    total_papers = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    db.close()

    return templates.TemplateResponse(request, "stats.html", {
        "stats": dict(stats) if stats else {},
        "weekly": weekly,
        "total_papers": total_papers,
    })


# ── Add Paper ───────────────────────────────────────────────

@app.post("/add-paper")
def add_paper(
    title: str = Form(...),
    authors: str = Form(...),
    year: int = Form(None),
    url: str = Form(""),
    field: str = Form(""),
    source: str = Form(""),
):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO papers (title, authors, year, url, field, source, type) VALUES (?, ?, ?, ?, ?, ?, 'modern')",
        (title, authors, year, url, field, source)
    )
    ensure_user_paper_entry(db, cursor.lastrowid)
    db.commit()
    db.close()
    return RedirectResponse(f"{ROOT_PATH}/explore", status_code=303)
