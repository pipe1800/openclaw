---
name: google-workspace
description: Google Workspace integration for Calendar, Drive, and Meet transcripts. List events, search files, read Meet transcripts. Use for checking schedules, finding documents, or processing meeting transcripts for syncing to other systems like Jira.
---

# Google Workspace

Access Google Calendar, Drive, and Meet transcripts via OAuth2.

## Setup

Environment variables required:
```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REFRESH_TOKEN="your-refresh-token"
```

To get a refresh token, run:
```bash
python scripts/google_auth.py login --client-id <id> --client-secret <secret>
```

## Quick Reference

### Script Location
```
scripts/google_api.py
```

Run with: `python scripts/google_api.py <command> [options]`

## Calendar

```bash
# List all calendars
python google_api.py list-calendars

# Today's events
python google_api.py today-events

# Upcoming events (next N hours)
python google_api.py upcoming-events --hours 48

# Events in date range
python google_api.py list-events --from 2026-02-01 --to 2026-02-07

# Specific calendar
python google_api.py today-events --calendar "work@example.com"
```

### Event Output
```json
{
  "id": "abc123",
  "summary": "Daily Standup",
  "start": "2026-02-03T08:30:00-06:00",
  "meetLink": "https://meet.google.com/xxx-xxxx-xxx",
  "location": null
}
```

## Drive

```bash
# List files
python google_api.py list-files --max 20

# Search files
python google_api.py search-files --query "project proposal"

# Get file metadata
python google_api.py get-file <file-id>

# Read file content (works for Google Docs, exports as text)
python google_api.py read-file <file-id>

# Download file
python google_api.py download-file <file-id> --output ./file.pdf

# Filter by type
python google_api.py list-files --type "application/pdf"
python google_api.py list-files --type "application/vnd.google-apps.document"
```

## Meet Transcripts

Meet transcripts are saved as Google Docs in Drive when transcription is enabled.

```bash
# List recent transcripts
python google_api.py list-transcripts --max 10

# List transcripts from a specific date
python google_api.py list-transcripts --from 2026-02-01

# Get transcript content by ID
python google_api.py get-transcript <file-id>

# Get the latest transcript (optionally filter by meeting name)
python google_api.py latest-transcript
python google_api.py latest-transcript --meeting "Daily"
```

### Transcript Workflow

1. Meeting ends → Google saves transcript to Drive
2. Search for it: `list-transcripts --from <today>`
3. Read content: `get-transcript <file-id>`
4. Parse and sync to Jira/other systems

## Common Patterns

### Check Daily Meeting Transcript
```bash
# Find today's daily standup transcript
python google_api.py latest-transcript --meeting "Daily"
```

### Find Documents by Name
```bash
python google_api.py search-files --query "Sprint Planning"
```

### Export Meeting Notes
```bash
# Get transcript and save to file
python google_api.py get-transcript <id> > meeting-notes.txt
```

## Transcript Format

Meet transcripts typically have this format:
```
Speaker Name
HH:MM

Spoken text here...

Another Speaker
HH:MM

Their text...
```

Parse by looking for lines with just a name followed by a timestamp.

## Error Handling

Common errors:
- **403**: API not enabled — enable in Google Cloud Console
- **401**: Token expired — refresh token should auto-refresh, but may need re-auth
- **404**: File not found — check file ID

## Tips

1. Transcripts appear in Drive shortly after meeting ends
2. Use `--meeting` filter to find specific recurring meetings
3. Calendar IDs: use `primary` for main calendar or full email for shared
4. Google Docs are exported as plain text when reading
