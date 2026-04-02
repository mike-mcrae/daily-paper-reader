import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
from app.database import get_db


def send_email(subject: str, html_body: str):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    email_to = os.getenv("EMAIL_TO", "")

    if not all([smtp_user, smtp_pass, email_to]):
        print("Email not configured — skipping send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True


def send_daily_paper_email(paper: dict):
    app_url = os.getenv("APP_URL", "http://localhost:8000")
    summary = paper.get("summary_text") or "No summary available yet."

    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
            Today's Economics Paper
        </h2>
        <h3 style="color: #2d3748;">{paper['title']}</h3>
        <p style="color: #718096;">{paper['authors']} ({paper['year']})</p>
        <p style="color: #718096;"><em>{paper['source']} &mdash; {paper['field']}</em></p>
        <div style="background: #f7fafc; padding: 15px; border-radius: 8px; margin: 15px 0;">
            {summary}
        </div>
        <a href="{app_url}" style="display: inline-block; background: #3182ce; color: white;
           padding: 10px 20px; border-radius: 6px; text-decoration: none; margin-top: 10px;">
            Open in App
        </a>
    </div>
    """
    return send_email("Today's Economics Paper", html)


def send_nudge_email(days_inactive: int, streak: int):
    app_url = os.getenv("APP_URL", "http://localhost:8000")

    if streak >= 5:
        subject = f"Incredible! {streak}-day streak!"
        message = f"You're on a {streak}-day reading streak. Keep the momentum going!"
    elif days_inactive == 2:
        subject = "Quick nudge: a paper awaits"
        message = "It's been a couple of days. A fresh paper is waiting for you."
    elif days_inactive in (3, 4):
        subject = "Don't break the chain!"
        message = f"It's been {days_inactive} days since you last read. Your streak is at risk!"
    else:
        subject = "Fresh start?"
        message = "It's been a while. No pressure — pick up where you left off, or start fresh today."

    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a365d;">{subject}</h2>
        <p style="color: #4a5568; font-size: 16px;">{message}</p>
        <a href="{app_url}" style="display: inline-block; background: #3182ce; color: white;
           padding: 10px 20px; border-radius: 6px; text-decoration: none; margin-top: 15px;">
            Read Today's Paper
        </a>
    </div>
    """
    return send_email(subject, html)


def check_and_send_nudge():
    db = get_db()
    stats = db.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()
    db.close()

    if not stats or not stats["last_active_date"]:
        return

    last_active = date.fromisoformat(stats["last_active_date"])
    today = date.today()
    days_inactive = 0
    d = today
    while d > last_active:
        if d.weekday() < 5:  # weekday
            days_inactive += 1
        d -= timedelta(days=1)

    if stats["current_streak"] >= 5:
        send_nudge_email(0, stats["current_streak"])
    elif days_inactive >= 2:
        send_nudge_email(days_inactive, stats["current_streak"])
