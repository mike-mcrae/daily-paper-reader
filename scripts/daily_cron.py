"""Morning cron: select today's paper and send email."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.database import init_db
from app.recommender import get_todays_paper
from app.email_service import send_daily_paper_email


def run():
    # Skip weekends
    if date.today().weekday() >= 5:
        print("Weekend — skipping.")
        return

    init_db()
    paper = get_todays_paper()
    if not paper:
        print("No paper available.")
        return

    print(f"Today's paper: {paper['title']}")

    try:
        sent = send_daily_paper_email(paper)
        if sent:
            print("Email sent.")
        else:
            print("Email not configured — skipped.")
    except Exception as e:
        print(f"Email failed: {e}")


if __name__ == "__main__":
    run()
