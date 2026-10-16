# Calendar Log System

Pulls upcoming events from a set of Google Calendars and logs them to STDOUT.

## Setup (Debian)

```sh
sudo apt install python3-venv
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

### Google auth (service account)

1. In Google Cloud Console, create a project and enable the **Google Calendar API**.
2. Create a **service account** and download a JSON key; save it as `service-account.json` (chmod 600).
3. In each Google Calendar's *Settings and sharing → Share with specific people*, add the service account's email. "See all event details" is enough for reading; use "Make changes to events" once we add event creation.
4. `cp config.example.json config.json` and list your calendar IDs (found under *Integrate calendar*).

## Usage

```sh
.venv/bin/python callog.py
# next days_ahead days, text output
.venv/bin/python callog.py -d 14 --json
# 14 days, JSON lines
```

Exits non-zero if any calendar fails (errors go to STDERR), so it's cron/systemd friendly.
