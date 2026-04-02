# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily Economics Paper Reader — a web app that recommends economics papers on weekdays, tracks reading status, stores structured notes, sends email reminders with gamified nudges, and builds a personal searchable paper library.

## Tech Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite
- **Frontend:** HTML + minimal JS (Jinja2 templates via FastAPI)
- **Email:** SMTP (Gmail or similar)
- **Hosting:** VPS with uvicorn, optional Nginx reverse proxy

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn main:app --host 0.0.0.0 --port 8000

# Seed the database (DB auto-initializes on app startup)
python scripts/seed_data.py

# Run daily cron tasks (paper selection + email)
python scripts/daily_cron.py

# Run evening nudge check
python scripts/nudge_cron.py
```

## Architecture

The full project spec lives in `AI INSTRUCTIONS.md`. Key design decisions:

- **No dynamic scraping in V1** — uses a static seed dataset (~300–500 papers as JSON) from top econ journals (AER, QJE, JPE, Econometrica, REStud) plus NBER/CEPR working papers.
- **Recommendation logic** is weighted random (40% classics, 30% modern, 20% working papers, 10% wildcard) with field diversity tracking and exclusion of already-read papers.
- **Gamification** counts only weekdays; a "successful day" = at least one paper marked "read" or "fully_noted". Streaks reset on missed weekdays.
- **Paper summaries** are generated once (template-based or lightweight LLM) and stored, not generated on the fly.
- **Single-user app** — no auth system in V1.

## Database Schema (SQLite)

Five tables: `papers`, `user_papers` (status tracking), `notes` (structured note fields), `daily_recommendations`, `user_stats` (streaks/totals). See `AI INSTRUCTIONS.md` for full schema.

## UI Pages

1. **Today** — daily paper with summary, status controls, notes link, replace button
2. **Explore** — browse/search/filter all papers
3. **Library** — tabs for Backlog/In Progress/Completed/Dropped
4. **Notes** — structured editor (summary, key findings, contribution, methodology, assumptions, improvements, quotes) with auto-save
5. **Stats** — streaks, totals, weekly progress

## Design Principles

- Keep it simple — this is a well-structured V1, not an over-engineered system.
- SQLite is the database; design for easy future upgrade but don't abstract prematurely.
- No heavy frontend frameworks — plain HTML/JS with Jinja2 templates.
- No embeddings, advanced AI, PDF storage, or mobile app in V1.
