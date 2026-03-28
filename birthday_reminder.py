#!/usr/bin/env python3
"""Birthday Reminder Sync

Reads birthdays from a local JSON file and prepares recurring Google Calendar
birthday reminder events using secure local config placeholders.
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

BIRTHDAYS_FILE = Path('birthdays_sample.json')
CONFIG_FILE = Path('config.local.json')


@dataclass
class BirthdayEntry:
    name: str
    birthday: str


def load_birthdays(path: Path) -> list[BirthdayEntry]:
    raw = json.loads(path.read_text(encoding='utf-8'))
    return [BirthdayEntry(**item) for item in raw]


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def next_birthday(birthday_str: str, today: date | None = None) -> date:
    today = today or date.today()
    born = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    candidate = date(today.year, born.month, born.day)
    if candidate < today:
        candidate = date(today.year + 1, born.month, born.day)
    return candidate


def upcoming_birthdays(entries: list[BirthdayEntry], days_ahead: int = 30) -> list[dict[str, Any]]:
    today = date.today()
    end = today + timedelta(days=days_ahead)
    upcoming = []
    for entry in entries:
        next_date = next_birthday(entry.birthday, today=today)
        if today <= next_date <= end:
            upcoming.append({
                'name': entry.name,
                'birthday': entry.birthday,
                'next_birthday': next_date.isoformat(),
                'days_until': (next_date - today).days,
            })
    return sorted(upcoming, key=lambda x: x['next_birthday'])


def refresh_access_token(config: dict[str, Any]) -> str:
    token_url = 'https://oauth2.googleapis.com/token'
    data = urllib.parse.urlencode({
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'refresh_token': config['refresh_token'],
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(token_url, data=data, method='POST')
    with urllib.request.urlopen(req) as response:
        payload = json.loads(response.read().decode())
    return payload['access_token']


def calendar_list_events(access_token: str, calendar_id: str, time_min: str, time_max: str) -> list[dict[str, Any]]:
    q = urllib.parse.urlencode({
        'timeMin': time_min,
        'timeMax': time_max,
        'singleEvents': 'true',
        'maxResults': '250',
    })
    url = f'https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(calendar_id, safe="")}/events?{q}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {access_token}')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    return data.get('items', [])


def event_exists(existing_events: list[dict[str, Any]], name: str, event_date: str) -> bool:
    target_summary = f'Birthday Reminder: {name}'
    for event in existing_events:
        summary = event.get('summary', '')
        start = event.get('start', {}).get('date') or event.get('start', {}).get('dateTime', '')[:10]
        if summary == target_summary and start == event_date:
            return True
    return False


def create_calendar_event(access_token: str, calendar_id: str, name: str, event_date: str, reminder_days: int = 7) -> dict[str, Any]:
    url = f'https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(calendar_id, safe="")}/events'
    payload = {
        'summary': f'Birthday Reminder: {name}',
        'description': f'Automatic birthday reminder for {name}.',
        'start': {'date': event_date},
        'end': {'date': event_date},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': reminder_days * 24 * 60},
                {'method': 'popup', 'minutes': 9 * 60},
            ],
        },
        'recurrence': ['RRULE:FREQ=YEARLY'],
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method='POST')
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def sync_birthdays(days_ahead: int = 30, dry_run: bool = True) -> list[dict[str, Any]]:
    birthdays = load_birthdays(BIRTHDAYS_FILE)
    upcoming = upcoming_birthdays(birthdays, days_ahead=days_ahead)
    if not upcoming:
        return []

    if dry_run:
        return upcoming

    config = load_config(CONFIG_FILE)
    access_token = refresh_access_token(config)
    today = date.today().isoformat() + 'T00:00:00Z'
    end = (date.today() + timedelta(days=days_ahead + 365)).isoformat() + 'T23:59:59Z'
    existing = calendar_list_events(access_token, config['calendar_id'], today, end)

    created = []
    for item in upcoming:
        if event_exists(existing, item['name'], item['next_birthday']):
            item['status'] = 'skipped_duplicate'
        else:
            event = create_calendar_event(access_token, config['calendar_id'], item['name'], item['next_birthday'], reminder_days=config.get('reminder_days', 7))
            item['status'] = 'created'
            item['event_id'] = event.get('id')
        created.append(item)
    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sync birthday reminders to Google Calendar securely.')
    parser.add_argument('--days', type=int, default=30, help='How many days ahead to scan for birthdays')
    parser.add_argument('--live', action='store_true', help='Perform live Google Calendar sync instead of dry run')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = sync_birthdays(days_ahead=args.days, dry_run=not args.live)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
