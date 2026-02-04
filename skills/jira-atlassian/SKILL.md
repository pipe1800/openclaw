---
name: jira-atlassian
description: Full Jira and Confluence integration. CRUD issues, transitions, comments, attachments, worklogs. Agile workflows with sprints, boards, epics. JQL search. Confluence pages and spaces. Use when managing tasks, bugs, stories, projects, sprints, or documentation in Jira/Atlassian Cloud.
---

# Jira & Atlassian Integration

Complete access to Jira Cloud and Confluence via REST API.

## Setup

Environment variables (set before using):
```bash
export JIRA_DOMAIN="https://your-domain.atlassian.net"
export JIRA_EMAIL="your@email.com"
export JIRA_API_TOKEN="your-api-token"
```

Get API token: https://id.atlassian.com/manage-profile/security/api-tokens

## Quick Reference

### Script Location
```
scripts/jira_api.py
```

Run with: `python scripts/jira_api.py <command> [options]`

### Issues

```bash
# Get issue
python jira_api.py get-issue PROJ-123

# Create issue
python jira_api.py create-issue --project PROJ --summary "Fix login bug" --type Bug

# With full options
python jira_api.py create-issue \
  --project PROJ \
  --summary "Implement feature X" \
  --type Story \
  --description "Detailed description here" \
  --priority High \
  --labels "backend,urgent" \
  --components "API,Auth"

# Update issue
python jira_api.py update-issue PROJ-123 --summary "New title" --priority Medium

# Delete issue
python jira_api.py delete-issue PROJ-123

# Search with JQL
python jira_api.py search --jql "project = PROJ AND status != Done" --max 50
```

### Transitions (Status Changes)

```bash
# See available transitions
python jira_api.py get-transitions PROJ-123

# Transition issue (by name or ID)
python jira_api.py transition PROJ-123 --to "In Progress"
python jira_api.py transition PROJ-123 --to "Done" --resolution "Fixed" --comment "Completed"
```

### Comments & Attachments

```bash
# Comments
python jira_api.py get-comments PROJ-123
python jira_api.py add-comment PROJ-123 --body "Looking into this now"

# Attachments
python jira_api.py get-attachments PROJ-123
python jira_api.py add-attachment PROJ-123 --file /path/to/file.pdf
python jira_api.py download-attachment 12345 --output ./downloaded.pdf
```

### Worklogs

```bash
python jira_api.py get-worklogs PROJ-123
python jira_api.py add-worklog PROJ-123 --time "2h 30m" --comment "Code review"
```

### Projects

```bash
python jira_api.py list-projects
python jira_api.py get-project PROJ
python jira_api.py get-project-components PROJ
python jira_api.py get-project-versions PROJ
```

### Agile: Boards & Sprints

```bash
# Boards
python jira_api.py list-boards --project PROJ
python jira_api.py get-board 42

# Sprints
python jira_api.py get-board-sprints 42 --state active
python jira_api.py get-sprint-issues 100

# Create sprint
python jira_api.py create-sprint --board 42 --name "Sprint 5" --goal "Complete auth module"

# Move issues to sprint
python jira_api.py move-to-sprint 100 --issues "PROJ-1,PROJ-2,PROJ-3"

# Update sprint
python jira_api.py update-sprint 100 --state closed
```

### Epics

```bash
python jira_api.py get-epic PROJ-50
python jira_api.py get-epic-issues PROJ-50
python jira_api.py move-to-epic PROJ-50 --issues "PROJ-51,PROJ-52"
```

### Users

```bash
python jira_api.py get-myself
python jira_api.py search-users --query "john"
python jira_api.py get-user 557058:f5678...  # account ID
```

### Metadata

```bash
python jira_api.py list-fields
python jira_api.py list-issue-types --project PROJ
python jira_api.py list-priorities
python jira_api.py list-statuses --project PROJ
python jira_api.py list-resolutions
```

### Confluence

```bash
# Spaces
python jira_api.py confluence-list-spaces
python jira_api.py confluence-get-space DEV

# Search
python jira_api.py confluence-search --cql 'space = DEV AND text ~ "API"'

# Pages
python jira_api.py confluence-get-page 12345

# Create page
python jira_api.py confluence-create-page \
  --space DEV \
  --title "New Documentation" \
  --body "<h1>Title</h1><p>Content here</p>"

# Update page (get current version first, then increment)
python jira_api.py confluence-update-page 12345 \
  --title "Updated Title" \
  --body "<h1>New Content</h1>" \
  --version 3
```

## JQL Cheatsheet

See `references/jql-guide.md` for full JQL documentation.

Common patterns:
- `assignee = currentUser() AND resolution = Unresolved` — My open work
- `project = PROJ AND sprint IN openSprints()` — Current sprint
- `project = PROJ AND created >= -7d` — Created this week
- `due < now() AND resolution = Unresolved` — Overdue

## Confluence Storage Format

See `references/confluence-guide.md` for CQL and XHTML storage format.

## Custom Fields

Pass custom fields as JSON:
```bash
python jira_api.py create-issue \
  --project PROJ \
  --summary "Task" \
  --type Task \
  --custom '{"customfield_10001": "value", "customfield_10002": 5}'
```

To find custom field IDs: `python jira_api.py list-fields`

## Common Workflows

### Create and Assign Bug
```bash
# Find user
python jira_api.py search-users --query "developer"

# Create bug assigned to them
python jira_api.py create-issue \
  --project PROJ \
  --summary "Login fails on mobile" \
  --type Bug \
  --priority High \
  --assignee "557058:abc..."
```

### Sprint Planning
```bash
# See backlog
python jira_api.py search --jql "project = PROJ AND sprint IS EMPTY AND status = Open"

# Move to sprint
python jira_api.py move-to-sprint 100 --issues "PROJ-10,PROJ-11,PROJ-12"
```

### Close Sprint
```bash
# Check remaining issues
python jira_api.py get-sprint-issues 100

# Close sprint
python jira_api.py update-sprint 100 --state closed
```

### Document a Feature
```bash
# Create Confluence page
python jira_api.py confluence-create-page \
  --space DEV \
  --title "Feature X Documentation" \
  --body "<h1>Overview</h1><p>Feature description...</p>"

# Link from Jira issue (add as comment with link)
python jira_api.py add-comment PROJ-100 --body "Documentation: https://your-domain.atlassian.net/wiki/spaces/DEV/pages/12345"
```

## Error Handling

The script exits with code 1 on errors and prints details to stderr. Common issues:

- **401**: Invalid credentials — check JIRA_EMAIL and JIRA_API_TOKEN
- **403**: No permission — verify project/issue access
- **404**: Not found — check issue key or ID exists
- **400**: Bad request — usually invalid field values, check the error message

## Tips

1. Use `--expand` on `get-issue` for full details including changelog
2. Transition names are case-insensitive
3. Assignee requires account ID, not email — use `search-users` to find it
4. Time format for worklogs: `2h`, `30m`, `1d`, `2h 30m`
5. Confluence pages require incrementing version on each update
