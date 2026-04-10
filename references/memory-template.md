# Memory Templates (v4.0)

Templates for initializing the v4.0 cognitive memory architecture with multi-mode dreaming.

---

## autodream.json

Location: `~/.openclaw/autodream/autodream.json`

Two profile presets are available. Select one during setup (see `SETUP.md`).

### Personal-assistant preset (default for personal/family/home-automation agents)

```json
{
  "version": "4.1",
  "profile": "personal-assistant",
  "activeModes": ["core", "rem", "deep"],
  "notificationLevel": "summary",
  "instanceName": "default",
  "timezone": "UTC",
  "modes": {
    "off": { "enabled": false },
    "core": {
      "enabled": true,
      "cadence": "0 3 * * *",
      "minScore": 0.72,
      "minRecallCount": 2,
      "minUnique": 1,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.90,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN", "PREFERENCE", "ROUTINE"]
    },
    "rem": {
      "enabled": true,
      "cadence": "30 4,10,16,22 * * *",
      "minScore": 0.85,
      "minRecallCount": 2,
      "minUnique": 2,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.88,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN", "PREFERENCE", "ROUTINE", "PROCEDURE"]
    },
    "deep": {
      "enabled": true,
      "cadence": "0 */12 * * *",
      "minScore": 0.80,
      "minRecallCount": 2,
      "minUnique": 2,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.86,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN", "PREFERENCE", "ROUTINE"]
    }
  },
  "lastRun": {
    "core": null,
    "rem": null,
    "deep": null
  }
}
```

### Business-employee preset (for supervisor DM / team GC / bounded workflow agents)

```json
{
  "version": "4.1",
  "profile": "business-employee",
  "activeModes": ["core", "rem", "deep"],
  "notificationLevel": "summary",
  "instanceName": "default",
  "timezone": "UTC",
  "modes": {
    "off": { "enabled": false },
    "core": {
      "enabled": true,
      "cadence": "0 3 * * *",
      "minScore": 0.72,
      "minRecallCount": 2,
      "minUnique": 1,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.92,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN"]
    },
    "rem": {
      "enabled": true,
      "cadence": "30 4,10,16,22 * * *",
      "minScore": 0.85,
      "minRecallCount": 3,
      "minUnique": 2,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.90,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN", "PROCEDURE"]
    },
    "deep": {
      "enabled": true,
      "cadence": "0 */12 * * *",
      "minScore": 0.80,
      "minRecallCount": 2,
      "minUnique": 2,
      "uniqueMode": "day_or_session",
      "fastPathMinScore": 0.88,
      "fastPathMinRecallCount": 2,
      "fastPathMarkers": ["HIGH", "PIN", "PROCEDURE"]
    }
  },
  "lastRun": {
    "core": null,
    "rem": null,
    "deep": null
  }
}
```

### autodream.json field reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | `"4.1"` | Config schema version |
| `profile` | string | — | Selected setup profile (`"personal-assistant"` or `"business-employee"`) |
| `activeModes` | string[] | `["core","rem","deep"]` | Modes enabled for cron dispatch |
| `notificationLevel` | string | `"summary"` | `"silent"`, `"summary"`, or `"full"` |
| `instanceName` | string | `"default"` | Human-readable instance identifier |
| `timezone` | string | `"UTC"` | IANA timezone for cron scheduling |
| `modes` | object | — | Per-mode gate thresholds |
| `modes.{name}.enabled` | boolean | — | Whether this mode is active |
| `modes.{name}.cadence` | string | — | Cron expression for this mode's schedule |
| `modes.{name}.minScore` | number | — | Minimum importance score to qualify |
| `modes.{name}.minRecallCount` | number | — | Minimum referenceCount to qualify |
| `modes.{name}.minUnique` | number | — | Minimum uniqueness count to qualify |
| `modes.{name}.uniqueMode` | string | `"day_or_session"` | How minUnique is evaluated: `"day_or_session"`, `"day"`, `"session"`, `"channel"`, `"max"` |
| `modes.{name}.fastPathMinScore` | number | — | Minimum importance for fast-path bypass |
| `modes.{name}.fastPathMinRecallCount` | number | — | Minimum recall count for fast-path bypass |
| `modes.{name}.fastPathMarkers` | string[] | — | Markers that trigger fast-path evaluation |
| `lastRun` | object | — | ISO timestamps of last completed run per mode |

---

## LTMEMORY.md

```markdown
# LTMEMORY.md — Long-Term Reflective Memory

_Last updated: YYYY-MM-DD_

> **Note:** This file is managed by Auto-Dream. MEMORY.md is managed by OpenClaw's native memory-core.
> Auto-Dream consolidates daily logs into structured long-term knowledge here.
> Native dreaming promotes high-signal durable facts to MEMORY.md separately.

---

## 🧠 Core Identity
<!-- Agent identity, name, purpose, personality -->

## 👤 User
<!-- User info, preferences, communication style -->

## 🏗️ Projects
<!-- Active projects, architecture, status -->

## 💰 Business
<!-- Metrics, revenue, unit economics -->

## 👥 People & Team
<!-- Team members, contacts, relationships -->

## 🎯 Strategy
<!-- Goals, plans, strategic decisions -->

## 📌 Key Decisions
<!-- Important decisions with dates -->

## 💡 Lessons Learned
<!-- Mistakes, insights, things that worked -->

## 🔧 Environment
<!-- Technical setup, tools, credentials (only if already stored) -->

## 🌊 Open Threads
<!-- Pending tasks, unresolved items -->
```

---

## memory/procedures.md

```markdown
# Procedures — How I Do Things

_Last updated: YYYY-MM-DD_

---

## 🎨 Communication Preferences
<!-- Language, tone, format preferences the user has expressed -->

## 🔧 Tool Workflows
<!-- Learned sequences for tools and integrations -->

## 📝 Format Preferences
<!-- How the user likes output structured -->

## ⚡ Shortcuts & Patterns
<!-- Recurring patterns, aliases, quick references -->
```

---

## memory/episodes/ structure

Each episode is a standalone markdown file tracking a project or significant event:

```markdown
# Episode: [Project/Event Name]

_Period: YYYY-MM-DD ~ YYYY-MM-DD_
_Status: active | completed | paused_
_Related: mem_xxx, mem_yyy_

---

## Timeline
<!-- Chronological entries, each with a date -->
- **YYYY-MM-DD** — What happened

## Key Decisions
<!-- Major choices made during this episode -->
- **YYYY-MM-DD** — Decision and rationale

## Lessons
<!-- What was learned from this episode -->
- Insight or takeaway
```

Naming convention: `memory/episodes/<kebab-case-name>.md`

---

## memory/index.json (v4.1 Schema)

```json
{
  "version": "4.1",
  "lastDream": null,
  "entries": [],
  "stats": {
    "totalEntries": 0,
    "avgImportance": 0,
    "lastPruned": null,
    "healthScore": 0,
    "healthMetrics": {
      "freshness": 0,
      "coverage": 0,
      "coherence": 0,
      "efficiency": 0,
      "reachability": 0
    },
    "insights": [],
    "healthHistory": [],
    "gateStats": {
      "lastCycleQualified": 0,
      "lastCycleDeferred": 0,
      "lastCycleBreakdown": { "rem": 0, "deep": 0, "core": 0 }
    }
  }
}
```

**Note:** Configuration fields (`notificationLevel`, `instanceName`, `timezone`, mode settings) have moved to `~/.openclaw/autodream/autodream.json`. The `index.json` now contains only runtime entry metadata and stats.

### stats fields

| Field | Type | Description |
|-------|------|-------------|
| `totalEntries` | number | Count of all non-archived entries |
| `avgImportance` | number | Mean importance score across all entries |
| `lastPruned` | string \| null | ISO timestamp of last archival operation |
| `healthScore` | number | Latest health score (0–100) |
| `healthMetrics` | object | Per-metric scores for the latest dream |
| `insights` | string[] | Latest dream insights (plain text, 1–3 items) |
| `healthHistory` | array | Chronological health snapshots (capped at 90) |
| `gateStats` | object | Quality gate results from the most recent cycle |

### Entry schema (v4.1)

Each object in `entries` follows this structure:

```json
{
  "id": "mem_001",
  "summary": "One-line summary of the memory entry",
  "source": "memory/2026-04-01.md",
  "target": "LTMEMORY.md#projects",
  "created": "2026-04-01",
  "lastReferenced": "2026-04-05",
  "referenceCount": 7,
  "uniqueSessionCount": 4,
  "sessionSources": [
    "memory/2026-04-01.md",
    "memory/2026-04-02.md",
    "memory/2026-04-04.md",
    "memory/2026-04-05.md"
  ],
  "uniqueDayCount": 4,
  "uniqueDaySources": [
    "2026-04-01",
    "2026-04-02",
    "2026-04-04",
    "2026-04-05"
  ],
  "promotedBy": "rem",
  "importance": 0.82,
  "tags": ["project", "architecture"],
  "related": ["mem_002", "mem_005"],
  "archived": false
}
```

Field reference:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID: `mem_NNN` (zero-padded to 3+ digits) |
| `summary` | string | One-line plain-text summary |
| `source` | string | File path where the raw info was found |
| `target` | string | File path + section where it was consolidated |
| `created` | string | ISO date when entry was first created |
| `lastReferenced` | string | ISO date when entry was last read/updated |
| `referenceCount` | number | Total times this entry has been referenced |
| `uniqueSessionCount` | number | Distinct sessions that referenced this entry |
| `sessionSources` | string[] | Last 30 session filenames that referenced this entry |
| `uniqueDayCount` | number | Distinct days that referenced this entry (derived from source path dates) |
| `uniqueDaySources` | string[] | Last 30 day strings (YYYY-MM-DD) that referenced this entry |
| `promotedBy` | string | Which dream mode promoted this entry (`"core"`, `"rem"`, `"deep"`, `"first-dream"`, `"manual"`) |
| `importance` | number | Computed score, 0.0–1.0 |
| `tags` | string[] | Categorization tags |
| `related` | string[] | IDs of related entries (undirected graph edges) |
| `archived` | boolean | True if moved to archive.md |

### v3.0 → v3.1 Migration

Existing v3.0 index.json entries need these additions:
1. Add `uniqueSessionCount` — set equal to `referenceCount` as initial estimate
2. Add `sessionSources` — set to `[entry.source]` as seed
3. Add `uniqueDayCount` — set to `uniqueSessionCount` as initial estimate (or derive from `sessionSources` dates)
4. Add `uniqueDaySources` — derive YYYY-MM-DD from existing `sessionSources` paths
5. Add `promotedBy` — set to `"core"` for all existing entries
6. Move `config` block from index.json to `~/.openclaw/autodream/autodream.json`
7. Add `gateStats` to stats block

---

## memory/.archive.md

```markdown
# Memory Archive

_Compressed entries that fell below importance threshold._

---

<!-- Format: [id] (created → archived) One-line summary -->
```

---

## memory/.dream-log.md

Starts as an empty file. Dream reports are appended after each cycle in the format defined in `dream-prompt-lite.md`.

---

## Directory structure summary

```
~/.openclaw/
├── autodream/
│   ├── autodream.json               # Dream mode configuration
│   └── autodream.json.bak           # Pre-change backup
│
workspace/
├── LTMEMORY.md                      # Long-term structured knowledge (Auto-Dream)
└── memory/
    ├── YYYY-MM-DD.md                # Daily logs (raw, append-only)
    ├── procedures.md                # Procedural memory
    ├── index.json                   # Entry metadata + stats (v4.1)
    ├── index.json.bak               # Pre-dream backup
    ├── .archive.md                  # Compressed old entries
    ├── .dream-log.md                # Dream cycle reports (append-only)
    ├── dashboard.html               # Generated health dashboard
    ├── export-YYYY-MM-DD.json       # Cross-instance migration bundles
    └── episodes/
        ├── project-alpha.md         # Episodic memory files (append-only)
        └── product-launch.md
```
