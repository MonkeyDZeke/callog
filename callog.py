#!/usr/bin/env python3
"""Pull upcoming events from a set of Google Calendars and log them to STDOUT."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]  # read/write for future event creation
DEFAULT_CONFIG = Path(__file__).with_name("config.json")


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    cfg.setdefault("days_ahead", 7)
    if not cfg.get("calendar_ids"):
        sys.exit("config: 'calendar_ids' must be a non-empty list")
    if not cfg.get("service_account_file"):
        sys.exit("config: 'service_account_file' is required")
    return cfg


def build_service(key_file):
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def fetch_events(service, calendar_id, time_min, time_max):
    """Yield single-occurrence events (recurrences expanded), handling pagination."""
    page_token = None
    while True:
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token,
        ).execute()
        yield from resp.get("items", [])
        page_token = resp.get("nextPageToken")
        if not page_token:
            return


def event_times(ev):
    """Return (start, end, all_day) from an event resource."""
    s, e = ev["start"], ev["end"]
    if "dateTime" in s:
        return s["dateTime"], e["dateTime"], False
    return s["date"], e["date"], True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-c", "--config", default=str(DEFAULT_CONFIG))
    p.add_argument("-d", "--days", type=int, help="override days_ahead from config")
    p.add_argument("--json", action="store_true", help="emit JSON lines instead of text")
    args = p.parse_args()

    cfg = load_config(args.config)
    days = args.days if args.days is not None else cfg["days_ahead"]
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days)).isoformat()

    service = build_service(cfg["service_account_file"])
    rows, failed = [], False

    for cal_id in cfg["calendar_ids"]:
        try:
            for ev in fetch_events(service, cal_id, time_min, time_max):
                if ev.get("status") == "cancelled":
                    continue
                start, end, all_day = event_times(ev)
                rows.append({
                    "calendar": cal_id,
                    "start": start,
                    "end": end,
                    "all_day": all_day,
                    "summary": ev.get("summary", "(no title)"),
                    "location": ev.get("location", ""),
                    "id": ev["id"],
                })
        except HttpError as exc:
            failed = True
            print(f"error: calendar {cal_id}: {exc}", file=sys.stderr)

    rows.sort(key=lambda r: r["start"])
    for r in rows:
        if args.json:
            print(json.dumps(r))
        else:
            loc = f" @ {r['location']}" if r["location"] else ""
            print(f"{r['start']} -> {r['end']} [{r['calendar']}] {r['summary']}{loc}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
