# JQL Quick Reference

JQL (Jira Query Language) is used to search for issues.

## Basic Syntax

```
field operator value [AND|OR field operator value]
```

## Common Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `status = "In Progress"` |
| `!=` | Not equals | `status != Done` |
| `~` | Contains text | `summary ~ "login"` |
| `!~` | Does not contain | `summary !~ "test"` |
| `>` `<` `>=` `<=` | Comparison | `created > -7d` |
| `IN` | In list | `status IN ("Open", "In Progress")` |
| `NOT IN` | Not in list | `priority NOT IN (Low, Lowest)` |
| `IS EMPTY` | Field is empty | `assignee IS EMPTY` |
| `IS NOT EMPTY` | Field has value | `fixVersion IS NOT EMPTY` |
| `WAS` | Historical value | `status WAS "Open"` |
| `CHANGED` | Field changed | `status CHANGED` |

## Date/Time Functions

| Function | Description |
|----------|-------------|
| `now()` | Current timestamp |
| `startOfDay()` | Start of today |
| `endOfDay()` | End of today |
| `startOfWeek()` | Start of current week |
| `startOfMonth()` | Start of current month |
| `-1d` / `-7d` | Relative days |
| `-1w` / `-4w` | Relative weeks |
| `"2024-01-15"` | Specific date |

## Common Fields

| Field | Description |
|-------|-------------|
| `project` | Project key or name |
| `status` | Issue status |
| `assignee` | Assigned user |
| `reporter` | Issue reporter |
| `priority` | Priority level |
| `issuetype` | Issue type (Bug, Task, etc.) |
| `created` | Creation date |
| `updated` | Last update date |
| `resolved` | Resolution date |
| `due` | Due date |
| `labels` | Issue labels |
| `component` | Project components |
| `fixVersion` | Fix version |
| `sprint` | Sprint name |
| `epic` | Epic link |
| `parent` | Parent issue (for subtasks) |
| `text` | Full-text search across fields |

## Useful JQL Examples

### My Work
```jql
assignee = currentUser() AND resolution = Unresolved
```

### Unassigned in Project
```jql
project = PROJ AND assignee IS EMPTY AND status != Done
```

### Recent Updates
```jql
project = PROJ AND updated >= -7d ORDER BY updated DESC
```

### Current Sprint
```jql
sprint IN openSprints() AND project = PROJ
```

### Bugs by Priority
```jql
project = PROJ AND issuetype = Bug AND resolution = Unresolved ORDER BY priority DESC
```

### Overdue Issues
```jql
due < now() AND resolution = Unresolved
```

### Created This Week
```jql
project = PROJ AND created >= startOfWeek()
```

### Issues Without Story Points
```jql
project = PROJ AND "Story Points" IS EMPTY AND issuetype = Story
```

### Blocked Issues
```jql
project = PROJ AND status = Blocked
```

### Issues Transitioned Today
```jql
status CHANGED DURING (startOfDay(), now())
```

### Issues I Commented On
```jql
issueFunction IN commented("by currentUser()")
```

### Epic and Its Stories
```jql
"Epic Link" = PROJ-100 OR key = PROJ-100
```

## ORDER BY Clause

```jql
project = PROJ ORDER BY created DESC, priority ASC
```

Common sort fields: `created`, `updated`, `priority`, `status`, `assignee`, `due`

## Tips

1. Quote values with spaces: `status = "In Progress"`
2. Use `currentUser()` for your assignments
3. Combine with `AND`/`OR` and parentheses for complex queries
4. `openSprints()` and `closedSprints()` for sprint filtering
5. Negative relative dates: `-1d`, `-1w`, `-1m`, `-1y`
