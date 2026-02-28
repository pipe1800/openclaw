---
name: session-logs
description: Search and analyze your own session logs (older/parent conversations) using jq and rg.
metadata: { "openclaw": { "emoji": "📜", "requires": { "bins": ["jq", "rg"] } } }
---

# session-logs

Search your complete conversation history stored in session JSONL files. Use this when a user references older/parent conversations or asks what was said before.

## Trigger

Use this skill when the user asks about prior chats, parent conversations, or historical context that isn't in memory files.

## Location

Session logs live at: `~/.openclaw/agents/<agentId>/sessions/` (use the `agent=<id>` value from the system prompt Runtime line).

- **`sessions.json`** - Index mapping session keys to session IDs
- **`<session-id>.jsonl`** - Full conversation transcript per session

## Structure

Each `.jsonl` file contains messages with:

- `type`: "session" (metadata) or "message"
- `timestamp`: ISO timestamp
- `message.role`: "user", "assistant", or "toolResult"
- `message.content[]`: Text, thinking, or tool calls (filter `type=="text"` for human-readable content)
- `message.usage.cost.total`: Cost per response

## Common Queries (PowerShell)

### List all sessions by date and size

```powershell
Get-ChildItem -Path ~/.openclaw/agents/<agentId>/sessions/*.jsonl | ForEach-Object {
    $date = (Get-Content $_.FullName -TotalCount 1 | jq -r '.timestamp').Split('T')[0]
    $size = [math]::Round($_.Length / 1MB, 2)
    [PSCustomObject]@{ Date = $date; SizeMB = $size; Name = $_.Name }
} | Sort-Object Date -Descending
```

### Find sessions from a specific day

```powershell
Get-ChildItem -Path ~/.openclaw/agents/<agentId>/sessions/*.jsonl | ForEach-Object {
    if ((Get-Content $_.FullName -TotalCount 1 | jq -r '.timestamp') -match "2026-01-06") {
        $_.FullName
    }
}
```

### Extract user messages from a session

```powershell
jq -r 'select(.message.role == \"user\") | .message.content[]? | select(.type == \"text\") | .text' <session>.jsonl
```

### Search for keyword in assistant responses

```powershell
jq -r 'select(.message.role == \"assistant\") | .message.content[]? | select(.type == \"text\") | .text' <session>.jsonl | rg -i "keyword"
```

### Get total cost for a session

```powershell
jq -s '[.[] | .message.usage.cost.total // 0] | add' <session>.jsonl
```

### Daily cost summary

```powershell
$costs = @{}
Get-ChildItem -Path ~/.openclaw/agents/<agentId>/sessions/*.jsonl | ForEach-Object {
    $date = (Get-Content $_.FullName -TotalCount 1 | jq -r '.timestamp').Split('T')[0]
    $cost = [double](jq -s '[.[] | .message.usage.cost.total // 0] | add' $_.FullName)
    $costs[$date] += $cost
}
$costs.GetEnumerator() | Sort-Object Name -Descending | ForEach-Object { "$($_.Name) `$$( [math]::Round($_.Value, 4) )" }
```

### Count messages and tokens in a session

```powershell
jq -s '{
  messages: length,
  user: [.[] | select(.message.role == \"user\")] | length,
  assistant: [.[] | select(.message.role == \"assistant\")] | length,
  first: .[0].timestamp,
  last: .[-1].timestamp
}' <session>.jsonl
```

### Tool usage breakdown

```powershell
jq -r '.message.content[]? | select(.type == \"toolCall\") | .name' <session>.jsonl | Group-Object | Sort-Object Count -Descending | Select-Object Count, Name
```

### Search across ALL sessions for a phrase

```powershell
rg -l "phrase" ~/.openclaw/agents/<agentId>/sessions/*.jsonl
```

## Tips

- Sessions are append-only JSONL (one JSON object per line)
- Large sessions can be several MB - use `Select-Object -First N` or `Get-Content -Tail N` for sampling
- The `sessions.json` index maps chat providers (discord, whatsapp, etc.) to session IDs
- Deleted sessions have `.deleted.<timestamp>` suffix

## Fast text-only hint (low noise)

```powershell
jq -r 'select(.type==\"message\") | .message.content[]? | select(.type==\"text\") | .text' ~/.openclaw/agents/<agentId>/sessions/<id>.jsonl | rg 'keyword'
```
