# Birthday Reminder Sync

A secure Python utility that reads birthdays from a local JSON file and creates recurring Google Calendar reminder events for upcoming birthdays.

## Features

- JSON birthday input
- Google Calendar API sync
- secure local config file with placeholders
- duplicate prevention
- dry-run mode by default
- fake sample data only
- GitHub-safe repo structure

## Security First

This repository is designed to be safe for GitHub:

- no real client secrets
- no real OAuth tokens
- no real calendar IDs
- no real names in sample data
- local secrets should live in `config.local.json`, which is ignored by git

Use placeholder values like:

```json
{
  "client_id": "XXXXXXXXXXXXXXXXXXXXXXXX",
  "client_secret": "XXXXXXXXXXXXXXXXXXXXXXXX",
  "refresh_token": "XXXXXXXXXXXXXXXXXXXXXXXX",
  "calendar_id": "________________________",
  "reminder_days": 7
}
```

## Project Structure

```bash
birthday-reminder-sync/
├── birthday_reminder.py
├── birthdays_sample.json
├── config.example.json
├── .gitignore
├── README.md
└── requirements.txt
```

## How It Works

1. Read birthdays from local JSON
2. Check which birthdays are coming up soon
3. Refresh Google OAuth access token using the local config
4. Check existing calendar events
5. Skip duplicates
6. Create recurring yearly birthday reminder events

## How to Run

### Dry run (safe default)
```bash
python3 birthday_reminder.py
```

### Scan a different time window
```bash
python3 birthday_reminder.py --days 60
```

### Live sync to Google Calendar
First copy `config.example.json` to `config.local.json` and fill in your real local secrets.

Then run:

```bash
python3 birthday_reminder.py --live
```

## Notes

- Keep `config.local.json` out of GitHub
- Use fake/sample birthdays for the public repo
- This script uses standard library HTTP requests only

## License

MIT
