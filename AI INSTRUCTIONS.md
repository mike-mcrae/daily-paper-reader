PROJECT: DAILY ECONOMICS PAPER READER (MVP → EXTENSIBLE)

GOAL:
Build a simple, clean web app (hosted on a VPS) that:
- Recommends at least 1 economics paper per weekday
- Allows flexible exploration of more papers
- Tracks reading status
- Stores structured notes
- Sends email reminders and gamified nudges
- Builds a personal searchable library of papers and notes

IMPORTANT:
This is a **simple but well-structured V1**. Do NOT over-engineer.
Design it so it can scale later.
We will push it to ssh mike@46.62.172.76
you have access to this vps and can push this repository to git from here and collect there etc. 

------------------------------------------------------------
TECH STACK (KEEP SIMPLE)
------------------------------------------------------------

Backend:
- Python + FastAPI

Database:
- SQLite (upgradeable later)

Frontend:
- Simple HTML + minimal JS (or Jinja templates via FastAPI)
- Clean, functional UI (no heavy frameworks)

Email:
- SMTP (Gmail or similar)

Hosting:
- Deploy on VPS (e.g. via systemd or Docker if desired)

------------------------------------------------------------
CORE FEATURES (MVP)
------------------------------------------------------------

1. DAILY PAPER RECOMMENDATION
2. PAPER LIBRARY (browse + search)
3. STATUS TRACKING
4. STRUCTURED NOTES
5. BACKLOG SYSTEM
6. EMAIL REMINDERS + NUDGES
7. SIMPLE GAMIFICATION (STREAKS)

------------------------------------------------------------
DATA SOURCES (INITIAL SIMPLE VERSION)
------------------------------------------------------------

Do NOT scrape dynamically for V1.

Instead:
- Build a **static seed dataset (JSON or CSV)** containing ~300–500 papers from:

    1. Top journals:
        - American Economic Review
        - Quarterly Journal of Economics
        - Journal of Political Economy
        - Econometrica
        - Review of Economic Studies

    2. Highly cited canonical papers

    3. Some recent papers (last ~5–10 years)

Structure each entry:

{
  "id": unique_id,
  "title": "...",
  "authors": "...",
  "year": 2001,
  "source": "AER / QJE / NBER / CEPR",
  "field": "IO / Macro / Labour / Political Economy / etc",
  "type": "classic / modern / working",
  "citation_proxy": number (approx or dummy),
  "url": "optional link"
}

NOTE:
Manually curate or semi-auto-generate this dataset.
No API integration in V1.

------------------------------------------------------------
RECOMMENDATION LOGIC (SIMPLE, NON-AI)
------------------------------------------------------------

Each weekday:
- Select 1 paper using weighted random draw:

    40% → classics (high citation / canonical)
    30% → modern top journal (last ~5–10 years)
    20% → working papers (NBER/CEPR)
    10% → wildcard (any field)

Rules:
- Avoid recommending papers already marked as:
    - read
    - fully_noted

- Prefer papers not yet shown

- Maintain field diversity:
    - track last ~5 papers’ fields
    - reduce probability of repeating same field

Store daily recommendation in DB.

------------------------------------------------------------
DATABASE SCHEMA
------------------------------------------------------------

TABLE: papers
- id (PK)
- title
- authors
- year
- source
- field
- type
- citation_proxy
- url

TABLE: user_papers
- id (PK)
- paper_id (FK)
- status (saved / started / read / fully_noted / skipped)
- date_added
- last_updated

TABLE: notes
- id (PK)
- paper_id (FK)
- summary
- key_findings
- contribution
- methodology
- assumptions_stated
- assumptions_unstated
- improvements
- quotes (TEXT)
- created_at
- updated_at

TABLE: daily_recommendations
- id (PK)
- date
- paper_id (FK)
- status (shown / replaced)

TABLE: user_stats
- id (PK)
- current_streak
- longest_streak
- total_read
- total_fully_noted
- last_active_date

------------------------------------------------------------
STATUSES (MANUAL ONLY)
------------------------------------------------------------

User can manually set:

- saved
- started
- read
- fully_noted
- skipped

------------------------------------------------------------
UI PAGES
------------------------------------------------------------

1. TODAY PAGE (MAIN)
- Show today’s paper:
    - title
    - authors
    - year
    - source
    - field
    - link (if exists)

- Show AI-style short summary (generated once, stored):
    - 3–5 bullet points (simple template-based for now)

- Actions:
    - Mark status (dropdown)
    - Add notes
    - Save to backlog
    - Replace paper (draw another)

------------------------------------------------------------

2. EXPLORE PAGE
- List all papers
- Filters:
    - field
    - type (classic / modern / working)
    - source
    - status

- Search:
    - title
    - authors

------------------------------------------------------------

3. LIBRARY PAGE
- Tabs:
    - Backlog (saved)
    - In Progress (started)
    - Completed (read / fully_noted)
    - Dropped (skipped)

------------------------------------------------------------

4. NOTES PAGE
- Open structured note editor for a paper:

Sections:
- Summary
- Key Findings
- Contribution
- Methodology
- Key Assumptions (Stated)
- Key Assumptions (Unstated)
- Improvements
- Quotes / Excerpts

Auto-save on edit.

------------------------------------------------------------

5. STATS PAGE
- Show:
    - Current streak (weekdays only)
    - Longest streak
    - Total papers read
    - Total fully noted
    - Simple weekly progress

------------------------------------------------------------
GAMIFICATION LOGIC
------------------------------------------------------------

- Only weekdays count (Mon–Fri)

- A “successful day”:
    - at least one paper marked as "read" OR "fully_noted"

- Streak increases if consecutive weekdays succeed

- Reset if weekday missed

------------------------------------------------------------
EMAIL SYSTEM
------------------------------------------------------------

Send daily email (weekday mornings):

Subject:
"Today's Economics Paper"

Body:
- Title
- Authors
- Short summary
- Link to app

------------------------------------------------------------

NUDGES:

If no activity:
- 2 days → gentle reminder
- 3–4 days → stronger encouragement
- 5+ days → “reset and restart” tone

If strong streak:
- congratulatory message

Tone:
- encouraging
- slightly gamified
- not aggressive

------------------------------------------------------------
SUMMARY GENERATION (SIMPLE)
------------------------------------------------------------

For each paper:
- Generate a short summary ONCE using template or lightweight LLM:

Store:
- summary_text

Displayed on Today page.

------------------------------------------------------------
MANUAL PAPER ADD
------------------------------------------------------------

Allow user to:
- add paper manually via:
    - title
    - authors
    - year
    - optional URL

Insert into papers table.

------------------------------------------------------------
SEARCH
------------------------------------------------------------

Basic:
- search titles and authors
- filter by field, type, status

------------------------------------------------------------
DEPLOYMENT
------------------------------------------------------------

- Run FastAPI app on VPS
- Use:
    uvicorn main:app --host 0.0.0.0 --port 8000

- Optional:
    - Nginx reverse proxy
    - HTTPS via certbot

- Run daily cron job:
    - generate daily paper
    - send emails

------------------------------------------------------------
CRON JOBS
------------------------------------------------------------

1. Daily (weekday morning):
    - select paper
    - store in DB
    - send email

2. Daily (evening):
    - check activity
    - send nudge if needed

------------------------------------------------------------
OUT OF SCOPE (FOR NOW)
------------------------------------------------------------

- No embeddings
- No advanced AI recommender
- No PDF storage
- No mobile app (web only)
- No complex UI frameworks

------------------------------------------------------------
DELIVERABLES
------------------------------------------------------------

Agent should produce:

1. Full project structure
2. Database initialization script
3. Seed dataset (JSON)
4. FastAPI backend
5. Basic frontend templates
6. Email system
7. Cron scripts
8. README with deployment instructions

------------------------------------------------------------
SUCCESS CRITERIA
------------------------------------------------------------

The app should:
- Load quickly
- Show 1 paper per day reliably
- Allow marking status easily
- Allow writing structured notes
- Maintain streaks
- Send daily emails

If those work cleanly → SUCCESS.

We iterate from there.