"""Evening cron: check activity and send nudge if needed."""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.database import init_db
from app.email_service import check_and_send_nudge


def run():
    if date.today().weekday() >= 5:
        print("Weekend — skipping.")
        return

    init_db()

    try:
        check_and_send_nudge()
        print("Nudge check complete.")
    except Exception as e:
        print(f"Nudge check failed: {e}")


if __name__ == "__main__":
    run()
