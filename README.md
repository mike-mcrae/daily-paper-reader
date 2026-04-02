# Daily Economics Paper Reader

A simple web app that recommends one economics paper per weekday, tracks reading status, stores structured notes, and sends email reminders with gamified streaks.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your SMTP credentials and app URL

# 3. Seed the database
python scripts/seed_data.py

# 4. Run the app
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

## VPS Deployment

### Systemd Service

Create `/etc/systemd/system/paper-reader.service`:

```ini
[Unit]
Description=Daily Paper Reader
After=network.target

[Service]
User=mike
WorkingDirectory=/home/mike/daily-paper-reader
ExecStart=/home/mike/daily-paper-reader/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/mike/daily-paper-reader/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable paper-reader
sudo systemctl start paper-reader
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then: `sudo certbot --nginx -d your-domain.com`

### Cron Jobs

```bash
crontab -e
```

```cron
# Morning: select paper + send email (weekdays 7am)
0 7 * * 1-5 cd /home/mike/daily-paper-reader && /home/mike/daily-paper-reader/venv/bin/python scripts/daily_cron.py

# Evening: send nudge if needed (weekdays 8pm)
0 20 * * 1-5 cd /home/mike/daily-paper-reader && /home/mike/daily-paper-reader/venv/bin/python scripts/nudge_cron.py
```

## Project Structure

```
main.py              # FastAPI app with all routes
app/
  database.py        # SQLite schema and connection
  recommender.py     # Weighted paper selection with field diversity
  email_service.py   # SMTP email (daily paper + nudges)
  streaks.py         # Weekday streak logic
scripts/
  seed_data.py       # Load seed papers into DB
  daily_cron.py      # Morning cron (paper + email)
  nudge_cron.py      # Evening cron (activity check)
data/
  seed_papers.json   # ~350 curated economics papers
templates/           # Jinja2 HTML templates
static/              # CSS
```
