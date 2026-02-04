#!/usr/bin/env python3
"""
Jira/Atlassian API Client - Full-featured wrapper for Jira Cloud REST API.

Usage:
    python jira_api.py <command> [options]

Environment Variables (or pass via args):
    JIRA_DOMAIN   - e.g., https://your-domain.atlassian.net
    JIRA_EMAIL    - Your Atlassian account email
    JIRA_API_TOKEN - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Commands:
    # Issues
    get-issue <issue-key>
    create-issue --project <key> --summary <text> --type <type> [--description <text>] [--assignee <id>] [--priority <name>] [--labels <l1,l2>] [--components <c1,c2>] [--custom <json>]
    update-issue <issue-key> [--summary <text>] [--description <text>] [--assignee <id>] [--priority <name>] [--labels <l1,l2>] [--components <c1,c2>] [--custom <json>]
    delete-issue <issue-key>
    search --jql <query> [--max <n>] [--fields <f1,f2>]
    
    # Transitions
    get-transitions <issue-key>
    transition <issue-key> --to <transition-id-or-name> [--comment <text>] [--resolution <name>]
    
    # Comments
    get-comments <issue-key>
    add-comment <issue-key> --body <text>
    
    # Attachments
    get-attachments <issue-key>
    add-attachment <issue-key> --file <path>
    download-attachment <attachment-id> --output <path>
    
    # Worklogs
    get-worklogs <issue-key>
    add-worklog <issue-key> --time <time-spent> [--comment <text>] [--started <datetime>]
    
    # Projects
    list-projects [--max <n>]
    get-project <project-key>
    get-project-components <project-key>
    get-project-versions <project-key>
    
    # Boards (Agile)
    list-boards [--project <key>] [--type <scrum|kanban>]
    get-board <board-id>
    get-board-sprints <board-id> [--state <active|closed|future>]
    get-sprint-issues <sprint-id> [--max <n>]
    
    # Sprints
    get-sprint <sprint-id>
    create-sprint --board <board-id> --name <name> [--start <date>] [--end <date>] [--goal <text>]
    update-sprint <sprint-id> [--name <name>] [--state <active|closed>] [--goal <text>]
    move-to-sprint <sprint-id> --issues <key1,key2,...>
    
    # Epics
    get-epic <epic-key>
    get-epic-issues <epic-key> [--max <n>]
    move-to-epic <epic-key> --issues <key1,key2,...>
    
    # Users
    search-users --query <text> [--max <n>]
    get-user <account-id>
    get-myself
    
    # Fields & Metadata
    list-fields
    list-issue-types [--project <key>]
    list-priorities
    list-statuses [--project <key>]
    list-resolutions
    
    # Confluence (if enabled)
    confluence-list-spaces [--max <n>]
    confluence-get-space <space-key>
    confluence-search --cql <query> [--max <n>]
    confluence-get-page <page-id> [--expand <body.storage,version>]
    confluence-create-page --space <key> --title <text> --body <html> [--parent <page-id>]
    confluence-update-page <page-id> --title <text> --body <html> --version <n>
"""

import argparse
import base64
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
import mimetypes


def get_auth():
    """Get authentication credentials from environment or fail."""
    domain = os.environ.get("JIRA_DOMAIN", "").rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    
    if not all([domain, email, token]):
        print("Error: Set JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN environment variables", file=sys.stderr)
        sys.exit(1)
    
    return domain, email, token


def make_request(method, url, data=None, headers=None, is_file=False):
    """Make an authenticated request to Jira API."""
    domain, email, token = get_auth()
    
    # Build auth header
    auth_string = f"{email}:{token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    
    default_headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Accept": "application/json",
    }
    
    if not is_file and data is not None:
        default_headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    
    if headers:
        default_headers.update(headers)
    
    full_url = f"{domain}{url}" if url.startswith("/") else url
    
    req = Request(full_url, data=data, headers=default_headers, method=method)
    
    try:
        with urlopen(req) as response:
            if response.status == 204:
                return None
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.loads(response.read().decode())
            return response.read()
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            try:
                error_json = json.loads(error_body)
                print(json.dumps(error_json, indent=2), file=sys.stderr)
            except:
                print(error_body, file=sys.stderr)
        sys.exit(1)


def get(url):
    return make_request("GET", url)


def post(url, data=None):
    return make_request("POST", url, data)


def put(url, data=None):
    return make_request("PUT", url, data)


def delete(url):
    return make_request("DELETE", url)


def upload_file(url, filepath):
    """Upload a file as multipart/form-data."""
    domain, email, token = get_auth()
    auth_string = f"{email}:{token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(filepath)
    mime_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    
    with open(filepath, "rb") as f:
        file_content = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()
    
    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Atlassian-Token": "no-check",
    }
    
    full_url = f"{domain}{url}" if url.startswith("/") else url
    req = Request(full_url, data=body, headers=headers, method="POST")
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            print(error_body, file=sys.stderr)
        sys.exit(1)


def output(data):
    """Print data as formatted JSON."""
    if data is not None:
        print(json.dumps(data, indent=2, default=str))


# ============ ISSUES ============

def cmd_get_issue(args):
    """Get issue details."""
    expand = "renderedFields,transitions,changelog" if args.expand else ""
    url = f"/rest/api/3/issue/{args.issue_key}"
    if expand:
        url += f"?expand={expand}"
    output(get(url))


def cmd_create_issue(args):
    """Create a new issue."""
    fields = {
        "project": {"key": args.project},
        "summary": args.summary,
        "issuetype": {"name": args.type},
    }
    
    if args.description:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": args.description}]}]
        }
    
    if args.assignee:
        fields["assignee"] = {"accountId": args.assignee}
    
    if args.priority:
        fields["priority"] = {"name": args.priority}
    
    if args.labels:
        fields["labels"] = args.labels.split(",")
    
    if args.components:
        fields["components"] = [{"name": c} for c in args.components.split(",")]
    
    if args.parent:
        fields["parent"] = {"key": args.parent}
    
    if args.custom:
        custom_fields = json.loads(args.custom)
        fields.update(custom_fields)
    
    output(post("/rest/api/3/issue", {"fields": fields}))


def cmd_update_issue(args):
    """Update an existing issue."""
    fields = {}
    
    if args.summary:
        fields["summary"] = args.summary
    
    if args.description:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": args.description}]}]
        }
    
    if args.assignee:
        fields["assignee"] = {"accountId": args.assignee} if args.assignee != "none" else None
    
    if args.priority:
        fields["priority"] = {"name": args.priority}
    
    if args.labels:
        fields["labels"] = args.labels.split(",")
    
    if args.components:
        fields["components"] = [{"name": c} for c in args.components.split(",")]
    
    if args.custom:
        custom_fields = json.loads(args.custom)
        fields.update(custom_fields)
    
    if fields:
        put(f"/rest/api/3/issue/{args.issue_key}", {"fields": fields})
        print(f"Issue {args.issue_key} updated successfully")


def cmd_delete_issue(args):
    """Delete an issue."""
    delete(f"/rest/api/3/issue/{args.issue_key}")
    print(f"Issue {args.issue_key} deleted successfully")


def cmd_search(args):
    """Search issues using JQL."""
    params = {
        "jql": args.jql,
        "maxResults": args.max or 50,
    }
    if args.fields:
        params["fields"] = args.fields.split(",")
    
    output(post("/rest/api/3/search/jql", params))


# ============ TRANSITIONS ============

def cmd_get_transitions(args):
    """Get available transitions for an issue."""
    output(get(f"/rest/api/3/issue/{args.issue_key}/transitions"))


def cmd_transition(args):
    """Transition an issue to a new status."""
    # First, get available transitions
    transitions = get(f"/rest/api/3/issue/{args.issue_key}/transitions")
    
    # Find the transition by ID or name
    transition_id = None
    for t in transitions.get("transitions", []):
        if str(t["id"]) == str(args.to) or t["name"].lower() == args.to.lower():
            transition_id = t["id"]
            break
    
    if not transition_id:
        print(f"Error: Transition '{args.to}' not found. Available transitions:", file=sys.stderr)
        for t in transitions.get("transitions", []):
            print(f"  - {t['id']}: {t['name']}", file=sys.stderr)
        sys.exit(1)
    
    data = {"transition": {"id": transition_id}}
    
    if args.comment:
        data["update"] = {
            "comment": [{
                "add": {
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": args.comment}]}]
                    }
                }
            }]
        }
    
    if args.resolution:
        data["fields"] = {"resolution": {"name": args.resolution}}
    
    post(f"/rest/api/3/issue/{args.issue_key}/transitions", data)
    print(f"Issue {args.issue_key} transitioned successfully")


# ============ COMMENTS ============

def cmd_get_comments(args):
    """Get all comments on an issue."""
    output(get(f"/rest/api/3/issue/{args.issue_key}/comment"))


def cmd_add_comment(args):
    """Add a comment to an issue."""
    data = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": args.body}]}]
        }
    }
    output(post(f"/rest/api/3/issue/{args.issue_key}/comment", data))


# ============ ATTACHMENTS ============

def cmd_get_attachments(args):
    """Get attachments for an issue."""
    issue = get(f"/rest/api/3/issue/{args.issue_key}?fields=attachment")
    output(issue.get("fields", {}).get("attachment", []))


def cmd_add_attachment(args):
    """Add an attachment to an issue."""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    output(upload_file(f"/rest/api/3/issue/{args.issue_key}/attachments", args.file))


def cmd_download_attachment(args):
    """Download an attachment."""
    attachment = get(f"/rest/api/3/attachment/{args.attachment_id}")
    content_url = attachment.get("content")
    
    domain, email, token = get_auth()
    auth_string = f"{email}:{token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    
    req = Request(content_url, headers={"Authorization": f"Basic {auth_bytes}"})
    
    with urlopen(req) as response:
        with open(args.output, "wb") as f:
            f.write(response.read())
    
    print(f"Downloaded to {args.output}")


# ============ WORKLOGS ============

def cmd_get_worklogs(args):
    """Get worklogs for an issue."""
    output(get(f"/rest/api/3/issue/{args.issue_key}/worklog"))


def cmd_add_worklog(args):
    """Add a worklog entry to an issue."""
    data = {"timeSpent": args.time}
    
    if args.comment:
        data["comment"] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": args.comment}]}]
        }
    
    if args.started:
        data["started"] = args.started
    
    output(post(f"/rest/api/3/issue/{args.issue_key}/worklog", data))


# ============ PROJECTS ============

def cmd_list_projects(args):
    """List all projects."""
    params = {"maxResults": args.max or 50}
    output(get(f"/rest/api/3/project/search?{urlencode(params)}"))


def cmd_get_project(args):
    """Get project details."""
    output(get(f"/rest/api/3/project/{args.project_key}"))


def cmd_get_project_components(args):
    """Get project components."""
    output(get(f"/rest/api/3/project/{args.project_key}/components"))


def cmd_get_project_versions(args):
    """Get project versions."""
    output(get(f"/rest/api/3/project/{args.project_key}/versions"))


# ============ BOARDS (AGILE) ============

def cmd_list_boards(args):
    """List all boards."""
    params = {"maxResults": args.max or 50}
    if args.project:
        params["projectKeyOrId"] = args.project
    if args.type:
        params["type"] = args.type
    
    output(get(f"/rest/agile/1.0/board?{urlencode(params)}"))


def cmd_get_board(args):
    """Get board details."""
    output(get(f"/rest/agile/1.0/board/{args.board_id}"))


def cmd_get_board_sprints(args):
    """Get sprints for a board."""
    params = {"maxResults": args.max or 50}
    if args.state:
        params["state"] = args.state
    
    output(get(f"/rest/agile/1.0/board/{args.board_id}/sprint?{urlencode(params)}"))


def cmd_get_sprint_issues(args):
    """Get issues in a sprint."""
    params = {"maxResults": args.max or 50}
    output(get(f"/rest/agile/1.0/sprint/{args.sprint_id}/issue?{urlencode(params)}"))


# ============ SPRINTS ============

def cmd_get_sprint(args):
    """Get sprint details."""
    output(get(f"/rest/agile/1.0/sprint/{args.sprint_id}"))


def cmd_create_sprint(args):
    """Create a new sprint."""
    data = {
        "originBoardId": int(args.board),
        "name": args.name,
    }
    
    if args.start:
        data["startDate"] = args.start
    if args.end:
        data["endDate"] = args.end
    if args.goal:
        data["goal"] = args.goal
    
    output(post("/rest/agile/1.0/sprint", data))


def cmd_update_sprint(args):
    """Update a sprint."""
    data = {}
    
    if args.name:
        data["name"] = args.name
    if args.state:
        data["state"] = args.state
    if args.goal:
        data["goal"] = args.goal
    
    if data:
        output(post(f"/rest/agile/1.0/sprint/{args.sprint_id}", data))


def cmd_move_to_sprint(args):
    """Move issues to a sprint."""
    data = {"issues": args.issues.split(",")}
    post(f"/rest/agile/1.0/sprint/{args.sprint_id}/issue", data)
    print(f"Moved issues to sprint {args.sprint_id}")


# ============ EPICS ============

def cmd_get_epic(args):
    """Get epic details."""
    output(get(f"/rest/agile/1.0/epic/{args.epic_key}"))


def cmd_get_epic_issues(args):
    """Get issues in an epic."""
    params = {"maxResults": args.max or 50}
    output(get(f"/rest/agile/1.0/epic/{args.epic_key}/issue?{urlencode(params)}"))


def cmd_move_to_epic(args):
    """Move issues to an epic."""
    data = {"issues": args.issues.split(",")}
    post(f"/rest/agile/1.0/epic/{args.epic_key}/issue", data)
    print(f"Moved issues to epic {args.epic_key}")


# ============ USERS ============

def cmd_search_users(args):
    """Search for users."""
    params = {"query": args.query, "maxResults": args.max or 50}
    output(get(f"/rest/api/3/user/search?{urlencode(params)}"))


def cmd_get_user(args):
    """Get user details by account ID."""
    output(get(f"/rest/api/3/user?accountId={args.account_id}"))


def cmd_get_myself(args):
    """Get current user details."""
    output(get("/rest/api/3/myself"))


# ============ FIELDS & METADATA ============

def cmd_list_fields(args):
    """List all fields."""
    output(get("/rest/api/3/field"))


def cmd_list_issue_types(args):
    """List issue types."""
    if args.project:
        output(get(f"/rest/api/3/project/{args.project}").get("issueTypes", []))
    else:
        output(get("/rest/api/3/issuetype"))


def cmd_list_priorities(args):
    """List priorities."""
    output(get("/rest/api/3/priority"))


def cmd_list_statuses(args):
    """List statuses."""
    if args.project:
        output(get(f"/rest/api/3/project/{args.project}/statuses"))
    else:
        output(get("/rest/api/3/status"))


def cmd_list_resolutions(args):
    """List resolutions."""
    output(get("/rest/api/3/resolution"))


# ============ CONFLUENCE ============

def cmd_confluence_list_spaces(args):
    """List Confluence spaces."""
    params = {"limit": args.max or 25}
    output(get(f"/wiki/api/v2/spaces?{urlencode(params)}"))


def cmd_confluence_get_space(args):
    """Get Confluence space details."""
    output(get(f"/wiki/api/v2/spaces/{args.space_key}"))


def cmd_confluence_search(args):
    """Search Confluence using CQL."""
    params = {"cql": args.cql, "limit": args.max or 25}
    output(get(f"/wiki/rest/api/content/search?{urlencode(params)}"))


def cmd_confluence_get_page(args):
    """Get Confluence page."""
    expand = args.expand or "body.storage,version"
    output(get(f"/wiki/rest/api/content/{args.page_id}?expand={expand}"))


def cmd_confluence_create_page(args):
    """Create a Confluence page."""
    data = {
        "type": "page",
        "title": args.title,
        "space": {"key": args.space},
        "body": {
            "storage": {
                "value": args.body,
                "representation": "storage"
            }
        }
    }
    
    if args.parent:
        data["ancestors"] = [{"id": args.parent}]
    
    output(post("/wiki/rest/api/content", data))


def cmd_confluence_update_page(args):
    """Update a Confluence page."""
    data = {
        "type": "page",
        "title": args.title,
        "body": {
            "storage": {
                "value": args.body,
                "representation": "storage"
            }
        },
        "version": {"number": int(args.version)}
    }
    
    output(put(f"/wiki/rest/api/content/{args.page_id}", data))


# ============ MAIN ============

def main():
    parser = argparse.ArgumentParser(description="Jira/Atlassian API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Issues
    p = subparsers.add_parser("get-issue", help="Get issue details")
    p.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")
    p.add_argument("--expand", action="store_true", help="Include expanded fields")
    p.set_defaults(func=cmd_get_issue)
    
    p = subparsers.add_parser("create-issue", help="Create a new issue")
    p.add_argument("--project", required=True, help="Project key")
    p.add_argument("--summary", required=True, help="Issue summary")
    p.add_argument("--type", required=True, help="Issue type (e.g., Task, Bug, Story)")
    p.add_argument("--description", help="Issue description")
    p.add_argument("--assignee", help="Assignee account ID")
    p.add_argument("--priority", help="Priority name")
    p.add_argument("--labels", help="Comma-separated labels")
    p.add_argument("--components", help="Comma-separated component names")
    p.add_argument("--parent", help="Parent issue key (for subtasks)")
    p.add_argument("--custom", help="Custom fields as JSON")
    p.set_defaults(func=cmd_create_issue)
    
    p = subparsers.add_parser("update-issue", help="Update an issue")
    p.add_argument("issue_key", help="Issue key")
    p.add_argument("--summary", help="New summary")
    p.add_argument("--description", help="New description")
    p.add_argument("--assignee", help="Assignee account ID (or 'none' to unassign)")
    p.add_argument("--priority", help="Priority name")
    p.add_argument("--labels", help="Comma-separated labels")
    p.add_argument("--components", help="Comma-separated component names")
    p.add_argument("--custom", help="Custom fields as JSON")
    p.set_defaults(func=cmd_update_issue)
    
    p = subparsers.add_parser("delete-issue", help="Delete an issue")
    p.add_argument("issue_key", help="Issue key")
    p.set_defaults(func=cmd_delete_issue)
    
    p = subparsers.add_parser("search", help="Search issues using JQL")
    p.add_argument("--jql", required=True, help="JQL query")
    p.add_argument("--max", type=int, help="Maximum results")
    p.add_argument("--fields", help="Comma-separated fields to return")
    p.set_defaults(func=cmd_search)
    
    # Transitions
    p = subparsers.add_parser("get-transitions", help="Get available transitions")
    p.add_argument("issue_key", help="Issue key")
    p.set_defaults(func=cmd_get_transitions)
    
    p = subparsers.add_parser("transition", help="Transition an issue")
    p.add_argument("issue_key", help="Issue key")
    p.add_argument("--to", required=True, help="Transition ID or name")
    p.add_argument("--comment", help="Transition comment")
    p.add_argument("--resolution", help="Resolution name (for Done transitions)")
    p.set_defaults(func=cmd_transition)
    
    # Comments
    p = subparsers.add_parser("get-comments", help="Get issue comments")
    p.add_argument("issue_key", help="Issue key")
    p.set_defaults(func=cmd_get_comments)
    
    p = subparsers.add_parser("add-comment", help="Add a comment")
    p.add_argument("issue_key", help="Issue key")
    p.add_argument("--body", required=True, help="Comment text")
    p.set_defaults(func=cmd_add_comment)
    
    # Attachments
    p = subparsers.add_parser("get-attachments", help="Get issue attachments")
    p.add_argument("issue_key", help="Issue key")
    p.set_defaults(func=cmd_get_attachments)
    
    p = subparsers.add_parser("add-attachment", help="Add an attachment")
    p.add_argument("issue_key", help="Issue key")
    p.add_argument("--file", required=True, help="File path")
    p.set_defaults(func=cmd_add_attachment)
    
    p = subparsers.add_parser("download-attachment", help="Download an attachment")
    p.add_argument("attachment_id", help="Attachment ID")
    p.add_argument("--output", required=True, help="Output file path")
    p.set_defaults(func=cmd_download_attachment)
    
    # Worklogs
    p = subparsers.add_parser("get-worklogs", help="Get issue worklogs")
    p.add_argument("issue_key", help="Issue key")
    p.set_defaults(func=cmd_get_worklogs)
    
    p = subparsers.add_parser("add-worklog", help="Add a worklog entry")
    p.add_argument("issue_key", help="Issue key")
    p.add_argument("--time", required=True, help="Time spent (e.g., 2h, 30m)")
    p.add_argument("--comment", help="Worklog comment")
    p.add_argument("--started", help="Start datetime (ISO format)")
    p.set_defaults(func=cmd_add_worklog)
    
    # Projects
    p = subparsers.add_parser("list-projects", help="List projects")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_list_projects)
    
    p = subparsers.add_parser("get-project", help="Get project details")
    p.add_argument("project_key", help="Project key")
    p.set_defaults(func=cmd_get_project)
    
    p = subparsers.add_parser("get-project-components", help="Get project components")
    p.add_argument("project_key", help="Project key")
    p.set_defaults(func=cmd_get_project_components)
    
    p = subparsers.add_parser("get-project-versions", help="Get project versions")
    p.add_argument("project_key", help="Project key")
    p.set_defaults(func=cmd_get_project_versions)
    
    # Boards
    p = subparsers.add_parser("list-boards", help="List boards")
    p.add_argument("--project", help="Filter by project")
    p.add_argument("--type", help="Board type (scrum/kanban)")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_list_boards)
    
    p = subparsers.add_parser("get-board", help="Get board details")
    p.add_argument("board_id", help="Board ID")
    p.set_defaults(func=cmd_get_board)
    
    p = subparsers.add_parser("get-board-sprints", help="Get board sprints")
    p.add_argument("board_id", help="Board ID")
    p.add_argument("--state", help="Sprint state filter (active/closed/future)")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_get_board_sprints)
    
    p = subparsers.add_parser("get-sprint-issues", help="Get sprint issues")
    p.add_argument("sprint_id", help="Sprint ID")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_get_sprint_issues)
    
    # Sprints
    p = subparsers.add_parser("get-sprint", help="Get sprint details")
    p.add_argument("sprint_id", help="Sprint ID")
    p.set_defaults(func=cmd_get_sprint)
    
    p = subparsers.add_parser("create-sprint", help="Create a sprint")
    p.add_argument("--board", required=True, help="Board ID")
    p.add_argument("--name", required=True, help="Sprint name")
    p.add_argument("--start", help="Start date (ISO format)")
    p.add_argument("--end", help="End date (ISO format)")
    p.add_argument("--goal", help="Sprint goal")
    p.set_defaults(func=cmd_create_sprint)
    
    p = subparsers.add_parser("update-sprint", help="Update a sprint")
    p.add_argument("sprint_id", help="Sprint ID")
    p.add_argument("--name", help="New name")
    p.add_argument("--state", help="New state (active/closed)")
    p.add_argument("--goal", help="New goal")
    p.set_defaults(func=cmd_update_sprint)
    
    p = subparsers.add_parser("move-to-sprint", help="Move issues to sprint")
    p.add_argument("sprint_id", help="Sprint ID")
    p.add_argument("--issues", required=True, help="Comma-separated issue keys")
    p.set_defaults(func=cmd_move_to_sprint)
    
    # Epics
    p = subparsers.add_parser("get-epic", help="Get epic details")
    p.add_argument("epic_key", help="Epic key")
    p.set_defaults(func=cmd_get_epic)
    
    p = subparsers.add_parser("get-epic-issues", help="Get epic issues")
    p.add_argument("epic_key", help="Epic key")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_get_epic_issues)
    
    p = subparsers.add_parser("move-to-epic", help="Move issues to epic")
    p.add_argument("epic_key", help="Epic key")
    p.add_argument("--issues", required=True, help="Comma-separated issue keys")
    p.set_defaults(func=cmd_move_to_epic)
    
    # Users
    p = subparsers.add_parser("search-users", help="Search users")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_search_users)
    
    p = subparsers.add_parser("get-user", help="Get user details")
    p.add_argument("account_id", help="Account ID")
    p.set_defaults(func=cmd_get_user)
    
    p = subparsers.add_parser("get-myself", help="Get current user")
    p.set_defaults(func=cmd_get_myself)
    
    # Fields & Metadata
    p = subparsers.add_parser("list-fields", help="List all fields")
    p.set_defaults(func=cmd_list_fields)
    
    p = subparsers.add_parser("list-issue-types", help="List issue types")
    p.add_argument("--project", help="Filter by project")
    p.set_defaults(func=cmd_list_issue_types)
    
    p = subparsers.add_parser("list-priorities", help="List priorities")
    p.set_defaults(func=cmd_list_priorities)
    
    p = subparsers.add_parser("list-statuses", help="List statuses")
    p.add_argument("--project", help="Filter by project")
    p.set_defaults(func=cmd_list_statuses)
    
    p = subparsers.add_parser("list-resolutions", help="List resolutions")
    p.set_defaults(func=cmd_list_resolutions)
    
    # Confluence
    p = subparsers.add_parser("confluence-list-spaces", help="List Confluence spaces")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_confluence_list_spaces)
    
    p = subparsers.add_parser("confluence-get-space", help="Get Confluence space")
    p.add_argument("space_key", help="Space key")
    p.set_defaults(func=cmd_confluence_get_space)
    
    p = subparsers.add_parser("confluence-search", help="Search Confluence")
    p.add_argument("--cql", required=True, help="CQL query")
    p.add_argument("--max", type=int, help="Maximum results")
    p.set_defaults(func=cmd_confluence_search)
    
    p = subparsers.add_parser("confluence-get-page", help="Get Confluence page")
    p.add_argument("page_id", help="Page ID")
    p.add_argument("--expand", help="Fields to expand")
    p.set_defaults(func=cmd_confluence_get_page)
    
    p = subparsers.add_parser("confluence-create-page", help="Create Confluence page")
    p.add_argument("--space", required=True, help="Space key")
    p.add_argument("--title", required=True, help="Page title")
    p.add_argument("--body", required=True, help="Page body (HTML)")
    p.add_argument("--parent", help="Parent page ID")
    p.set_defaults(func=cmd_confluence_create_page)
    
    p = subparsers.add_parser("confluence-update-page", help="Update Confluence page")
    p.add_argument("page_id", help="Page ID")
    p.add_argument("--title", required=True, help="Page title")
    p.add_argument("--body", required=True, help="Page body (HTML)")
    p.add_argument("--version", required=True, help="Current version number + 1")
    p.set_defaults(func=cmd_confluence_update_page)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
