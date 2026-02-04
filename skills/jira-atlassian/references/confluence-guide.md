# Confluence Quick Reference

## CQL (Confluence Query Language)

Search syntax for Confluence content.

### Basic Operators

| Operator | Example |
|----------|---------|
| `=` | `space = "DEV"` |
| `~` | `title ~ "meeting"` |
| `AND` / `OR` | `space = DEV AND type = page` |

### Common Fields

| Field | Description |
|-------|-------------|
| `space` | Space key |
| `title` | Page title |
| `text` | Page content |
| `type` | `page`, `blogpost`, `comment`, `attachment` |
| `creator` | Who created it |
| `created` | Creation date |
| `lastmodified` | Last modification date |
| `label` | Page labels |
| `ancestor` | Parent page ID |

### Date Filters

```cql
created > "2024-01-01"
lastmodified >= now("-7d")
```

### Example Queries

Recent pages in space:
```cql
space = DEV AND type = page AND lastmodified >= now("-7d")
```

Pages by label:
```cql
label = "documentation" AND space = TEAM
```

Search content:
```cql
text ~ "API specification" AND type = page
```

## Page Storage Format

Confluence uses XHTML-based storage format. Common elements:

### Basic Structure

```html
<p>Paragraph text</p>

<h1>Heading 1</h1>
<h2>Heading 2</h2>

<ul>
  <li>Bullet item</li>
</ul>

<ol>
  <li>Numbered item</li>
</ol>
```

### Rich Content

**Links:**
```html
<ac:link>
  <ri:page ri:content-title="Page Name" ri:space-key="SPACE"/>
</ac:link>
```

**Code Block:**
```html
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[print("Hello")]]></ac:plain-text-body>
</ac:structured-macro>
```

**Info Panel:**
```html
<ac:structured-macro ac:name="info">
  <ac:rich-text-body><p>Info message</p></ac:rich-text-body>
</ac:structured-macro>
```

**Warning Panel:**
```html
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body><p>Warning message</p></ac:rich-text-body>
</ac:structured-macro>
```

**Table:**
```html
<table>
  <tbody>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
    <tr>
      <td>Cell 1</td>
      <td>Cell 2</td>
    </tr>
  </tbody>
</table>
```

**Status Macro:**
```html
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">DONE</ac:parameter>
</ac:structured-macro>
```

## Common Patterns

### Creating Documentation Page

```html
<h1>Overview</h1>
<p>Brief description of the topic.</p>

<ac:structured-macro ac:name="toc"/>

<h2>Getting Started</h2>
<p>Introduction content...</p>

<h2>Details</h2>
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[npm install package]]></ac:plain-text-body>
</ac:structured-macro>

<h2>See Also</h2>
<ul>
  <li><ac:link><ri:page ri:content-title="Related Page"/></ac:link></li>
</ul>
```

### Meeting Notes Template

```html
<h2>Attendees</h2>
<ul>
  <li>@person1</li>
  <li>@person2</li>
</ul>

<h2>Agenda</h2>
<ol>
  <li>Topic 1</li>
  <li>Topic 2</li>
</ol>

<h2>Discussion</h2>
<p>Notes from the meeting...</p>

<h2>Action Items</h2>
<ac:task-list>
  <ac:task>
    <ac:task-body>Task description <ac:link><ri:user ri:account-id="user-id"/></ac:link></ac:task-body>
  </ac:task>
</ac:task-list>
```

## Tips

1. Always increment version number when updating pages
2. Get current version with `confluence-get-page` before updating
3. Use labels for organization and searchability
4. Parent pages create hierarchical navigation
5. Test XHTML in the Confluence editor before API updates
