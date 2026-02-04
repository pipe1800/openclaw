#!/usr/bin/env python3
"""
Google Workspace API Client - Drive, Calendar, and Meet transcript access.

Usage:
    python google_api.py <command> [options]

Environment Variables:
    GOOGLE_CLIENT_ID     - OAuth2 client ID
    GOOGLE_CLIENT_SECRET - OAuth2 client secret  
    GOOGLE_REFRESH_TOKEN - Refresh token

Commands:
    # Calendar
    list-calendars
    list-events [--calendar <id>] [--from <date>] [--to <date>] [--max <n>]
    get-event <event-id> [--calendar <id>]
    today-events [--calendar <id>]
    upcoming-events [--hours <n>] [--calendar <id>]

    # Drive
    list-files [--query <q>] [--folder <id>] [--max <n>] [--type <mime-type>]
    get-file <file-id>
    download-file <file-id> --output <path>
    read-file <file-id>  # Read text content (for docs/transcripts)
    search-files --query <text> [--max <n>]

    # Meet Transcripts
    list-transcripts [--from <date>] [--max <n>]
    get-transcript <file-id>
    latest-transcript [--meeting <name>]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote
from urllib.error import HTTPError


def get_credentials():
    """Get OAuth credentials from environment."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("Error: Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN", file=sys.stderr)
        sys.exit(1)
    
    return client_id, client_secret, refresh_token


def get_access_token():
    """Get a fresh access token."""
    client_id, client_secret, refresh_token = get_credentials()
    
    data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    
    req = Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    
    try:
        with urlopen(req) as response:
            tokens = json.loads(response.read().decode())
            return tokens["access_token"]
    except HTTPError as e:
        error = e.read().decode()
        print(f"Auth Error: {error}", file=sys.stderr)
        sys.exit(1)


def api_request(url, method="GET", data=None):
    """Make an authenticated API request."""
    token = get_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    
    if data:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    
    req = Request(url, data=data, headers=headers, method=method)
    
    try:
        with urlopen(req) as response:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.loads(response.read().decode())
            return response.read()
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            try:
                print(json.dumps(json.loads(error_body), indent=2), file=sys.stderr)
            except:
                print(error_body, file=sys.stderr)
        sys.exit(1)


def output(data):
    """Print JSON output."""
    if data is not None:
        print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


# ============ CALENDAR ============

def cmd_list_calendars(args):
    """List all calendars."""
    result = api_request("https://www.googleapis.com/calendar/v3/users/me/calendarList")
    output(result)


def cmd_list_events(args):
    """List calendar events."""
    calendar_id = args.calendar or "primary"
    
    params = {
        "maxResults": args.max or 50,
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    
    if args.from_date:
        params["timeMin"] = f"{args.from_date}T00:00:00Z"
    if args.to_date:
        params["timeMax"] = f"{args.to_date}T23:59:59Z"
    
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events?{urlencode(params)}"
    result = api_request(url)
    output(result)


def cmd_get_event(args):
    """Get a specific event."""
    calendar_id = args.calendar or "primary"
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events/{args.event_id}"
    result = api_request(url)
    output(result)


def cmd_today_events(args):
    """Get today's events."""
    calendar_id = args.calendar or "primary"
    today = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "timeMin": f"{today}T00:00:00Z",
        "timeMax": f"{today}T23:59:59Z",
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events?{urlencode(params)}"
    result = api_request(url)
    
    # Simplify output
    events = []
    for event in result.get("items", []):
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        events.append({
            "id": event.get("id"),
            "summary": event.get("summary"),
            "start": start,
            "meetLink": event.get("hangoutLink"),
            "location": event.get("location"),
        })
    
    output(events)


def cmd_upcoming_events(args):
    """Get events in the next N hours."""
    calendar_id = args.calendar or "primary"
    hours = args.hours or 24
    
    now = datetime.utcnow()
    end = now + timedelta(hours=hours)
    
    params = {
        "timeMin": now.isoformat() + "Z",
        "timeMax": end.isoformat() + "Z",
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events?{urlencode(params)}"
    result = api_request(url)
    
    events = []
    for event in result.get("items", []):
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        events.append({
            "id": event.get("id"),
            "summary": event.get("summary"),
            "start": start,
            "meetLink": event.get("hangoutLink"),
        })
    
    output(events)


# ============ DRIVE ============

def cmd_list_files(args):
    """List files in Drive."""
    params = {
        "pageSize": args.max or 50,
        "fields": "files(id,name,mimeType,createdTime,modifiedTime,webViewLink)",
    }
    
    q_parts = []
    if args.query:
        q_parts.append(args.query)
    if args.folder:
        q_parts.append(f"'{args.folder}' in parents")
    if args.type:
        q_parts.append(f"mimeType='{args.type}'")
    
    if q_parts:
        params["q"] = " and ".join(q_parts)
    
    url = f"https://www.googleapis.com/drive/v3/files?{urlencode(params)}"
    result = api_request(url)
    output(result)


def cmd_get_file(args):
    """Get file metadata."""
    url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}?fields=*"
    result = api_request(url)
    output(result)


def cmd_download_file(args):
    """Download a file."""
    token = get_access_token()
    url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}?alt=media"
    
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    
    try:
        with urlopen(req) as response:
            with open(args.output, "wb") as f:
                f.write(response.read())
        print(f"Downloaded to {args.output}")
    except HTTPError as e:
        print(f"Error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_read_file(args):
    """Read text content of a file (Google Docs exported as text)."""
    token = get_access_token()
    
    # First get file metadata to check type
    meta_url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}?fields=mimeType,name"
    meta = api_request(meta_url)
    mime_type = meta.get("mimeType", "")
    
    # Google Docs need export, regular files can be downloaded directly
    if mime_type == "application/vnd.google-apps.document":
        url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}/export?mimeType=text/plain"
    else:
        url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}?alt=media"
    
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    
    try:
        with urlopen(req) as response:
            content = response.read().decode("utf-8", errors="replace")
            # Handle Windows encoding issues
            sys.stdout.buffer.write(content.encode("utf-8", errors="replace"))
            sys.stdout.buffer.write(b"\n")
    except HTTPError as e:
        print(f"Error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_search_files(args):
    """Search for files by name/content."""
    params = {
        "pageSize": args.max or 20,
        "fields": "files(id,name,mimeType,createdTime,modifiedTime)",
        "q": f"fullText contains '{args.query}' or name contains '{args.query}'",
    }
    
    url = f"https://www.googleapis.com/drive/v3/files?{urlencode(params)}"
    result = api_request(url)
    output(result)


# ============ MEET TRANSCRIPTS ============

def cmd_list_transcripts(args):
    """List Meet transcripts (stored as Google Docs in Drive)."""
    # Meet transcripts are Google Docs with specific naming pattern
    q = "mimeType='application/vnd.google-apps.document' and name contains 'Transcript'"
    
    if args.from_date:
        q += f" and createdTime >= '{args.from_date}T00:00:00'"
    
    params = {
        "pageSize": args.max or 20,
        "fields": "files(id,name,createdTime,modifiedTime,webViewLink)",
        "q": q,
        "orderBy": "createdTime desc",
    }
    
    url = f"https://www.googleapis.com/drive/v3/files?{urlencode(params)}"
    result = api_request(url)
    output(result)


def cmd_get_transcript(args):
    """Get a Meet transcript content."""
    token = get_access_token()
    
    # Export as plain text
    url = f"https://www.googleapis.com/drive/v3/files/{args.file_id}/export?mimeType=text/plain"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    
    try:
        with urlopen(req) as response:
            content = response.read().decode("utf-8", errors="replace")
            print(content)
    except HTTPError as e:
        print(f"Error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_latest_transcript(args):
    """Get the most recent transcript, optionally filtered by meeting name."""
    q = "mimeType='application/vnd.google-apps.document' and name contains 'Transcript'"
    
    if args.meeting:
        q += f" and name contains '{args.meeting}'"
    
    params = {
        "pageSize": 1,
        "fields": "files(id,name,createdTime)",
        "q": q,
        "orderBy": "createdTime desc",
    }
    
    url = f"https://www.googleapis.com/drive/v3/files?{urlencode(params)}"
    result = api_request(url)
    
    files = result.get("files", [])
    if not files:
        print("No transcripts found", file=sys.stderr)
        sys.exit(1)
    
    # Get the content
    file_id = files[0]["id"]
    print(f"# {files[0]['name']}", file=sys.stderr)
    print(f"# Created: {files[0]['createdTime']}", file=sys.stderr)
    print("", file=sys.stderr)
    
    token = get_access_token()
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    
    with urlopen(req) as response:
        content = response.read().decode("utf-8", errors="replace")
        print(content)


# ============ MAIN ============

def main():
    parser = argparse.ArgumentParser(description="Google Workspace API Client")
    subparsers = parser.add_subparsers(dest="command")
    
    # Calendar commands
    p = subparsers.add_parser("list-calendars", help="List calendars")
    p.set_defaults(func=cmd_list_calendars)
    
    p = subparsers.add_parser("list-events", help="List events")
    p.add_argument("--calendar", help="Calendar ID (default: primary)")
    p.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    p.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_list_events)
    
    p = subparsers.add_parser("get-event", help="Get event details")
    p.add_argument("event_id", help="Event ID")
    p.add_argument("--calendar", help="Calendar ID")
    p.set_defaults(func=cmd_get_event)
    
    p = subparsers.add_parser("today-events", help="Get today's events")
    p.add_argument("--calendar", help="Calendar ID")
    p.set_defaults(func=cmd_today_events)
    
    p = subparsers.add_parser("upcoming-events", help="Get upcoming events")
    p.add_argument("--hours", type=int, help="Hours ahead (default: 24)")
    p.add_argument("--calendar", help="Calendar ID")
    p.set_defaults(func=cmd_upcoming_events)
    
    # Drive commands
    p = subparsers.add_parser("list-files", help="List files")
    p.add_argument("--query", help="Drive query")
    p.add_argument("--folder", help="Folder ID")
    p.add_argument("--type", help="MIME type filter")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_list_files)
    
    p = subparsers.add_parser("get-file", help="Get file metadata")
    p.add_argument("file_id", help="File ID")
    p.set_defaults(func=cmd_get_file)
    
    p = subparsers.add_parser("download-file", help="Download file")
    p.add_argument("file_id", help="File ID")
    p.add_argument("--output", required=True, help="Output path")
    p.set_defaults(func=cmd_download_file)
    
    p = subparsers.add_parser("read-file", help="Read file content as text")
    p.add_argument("file_id", help="File ID")
    p.set_defaults(func=cmd_read_file)
    
    p = subparsers.add_parser("search-files", help="Search files")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_search_files)
    
    # Transcript commands
    p = subparsers.add_parser("list-transcripts", help="List Meet transcripts")
    p.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_list_transcripts)
    
    p = subparsers.add_parser("get-transcript", help="Get transcript content")
    p.add_argument("file_id", help="Transcript file ID")
    p.set_defaults(func=cmd_get_transcript)
    
    p = subparsers.add_parser("latest-transcript", help="Get latest transcript")
    p.add_argument("--meeting", help="Filter by meeting name")
    p.set_defaults(func=cmd_latest_transcript)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
