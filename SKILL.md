---
name: auto-dream
description: "Cognitive memory architecture for OpenClaw agents — multi-mode dream cycles that consolidate daily logs into structured long-term memory with quality gates, importance scoring, insights, and push notifications. Use when: user asks for 'auto memory', 'dream', 'auto-dream', 'memory consolidation', 'memory dashboard', 'export memory', 'dream mode'."
---

# Auto Dream — Memory Consolidation System

Agent periodically "dreams" — scans daily logs, extracts key knowledge, applies quality gates based on the active dream mode, consolidates qualifying entries into long-term memory, and sends a summary report to the user.

## Core Files

| File | Purpose | Mutability |
|------|---------|------------|
| `~/.openclaw/autodream/autodream.json` | Dream mode configuration | User-editable |
| `LTMEMORY.md` | Structured long-term knowledge (Auto-Dream layer) | Append, update, archive |
| `memory/procedures.md` | Workflow preferences, tool usage | Append, update |
| `memory/episodes/*.md` | Project narratives | Append only |
| `memory/index.json` | Runtime entry metadata (v4.1 schema) | Rebuilt each dream |
| `memory/.dream-log.md` | Dream report log | Append only |
| `memory/.archive.md` | Low-importance compressed archive | Append only |

Optional: LCM plugin (Working Memory layer). If not installed, prompt the user:
> "Recommended: install the LCM plugin for working memory: `openclaw plugins install @martian-engineering/lossless-claw`"

Do not auto-install plugins or modify config.

## Runtime Profile

Auto-Dream reads thresholds from `~/.openclaw/autodream/autodream.json`.
Profile selection is setup-time only and is persisted in the `"profile"` field.
The gate logic reads config generically.

## Dream Modes

Four modes control consolidation frequency and quality gates. An entry must pass **all three gates** for its mode before it is promoted to long-term memory.

Default thresholds vary by profile. The values below are the **personal-assistant** defaults. See `profiles/business-employee.md` for business defaults.

| Mode | Cadence | minScore | minRecallCount | minUnique | Purpose |
|------|---------|----------|----------------|-----------|---------|
| `off` | Disabled | — | — | — | No dreaming |
| `core` | Daily 3 AM | 0.72 | 2 | 1 | Daily sweep — catches everything reasonably important |
| `rem` | Every 6 hours | 0.85 | 2 | 2 | High-frequency — fast-tracks clearly high-signal entries |
| `deep` | Every 12 hours | 0.80 | 2 | 2 | Mid-frequency — catches warm entries with cross-day breadth |

### Gate Definitions

- **minScore** — minimum `importance` score (0.0–1.0) computed from `base_weight × recency × reference_boost / 8.0`. See `references/scoring.md`.
- **minRecallCount** — minimum `referenceCount` in `index.json`. How many times this entry has been referenced across any context.
- **minUnique** — minimum uniqueness count. The meaning of "unique" depends on `uniqueMode`.

### uniqueMode

Controls how `minUnique` is evaluated:

| uniqueMode | Behavior |
|------------|----------|
| `day_or_session` | **(default)** Prefer `uniqueDayCount` when available, fall back to `uniqueSessionCount` |
| `day` | Use `uniqueDayCount` only |
| `session` | Use `uniqueSessionCount` only (legacy behavior) |
| `channel` | Use `uniqueChannelCount` only |
| `max` | Use the highest of day, session, and channel counts |

`day_or_session` is the default for both profiles. It allows day-based reinforcement — if the same truth is referenced on different days, it counts even if the sessions overlap. This is important for narrow-topology agents (personal assistants, home-automation) where the owner is the primary interaction source.

### Fast-path markers

Entries with specific markers can bypass the regular AND gate through a softer fast-path check. The fast-path requires either:

- **Score + recall pass:** `importance >= fastPathMinScore AND referenceCount >= fastPathMinRecallCount`
- **Marker match:** entry marker is in `fastPathMarkers` list

`PERMANENT` still bypasses all gates unconditionally. Fast-path is a softer bypass for high-salience entries that don't quite meet the regular gate thresholds.

Available markers: `HIGH`, `PIN`, `PREFERENCE`, `ROUTINE`, `PROCEDURE`. Which markers are active depends on the profile preset written during setup.

### Mode Dispatch (Single Cron)

One cron runs 4 times daily (4:30, 10:30, 16:30, 22:30). On each trigger, the dream prompt reads `autodream.json` and checks elapsed time since last run of each mode:

```
elapsed_since_last_rem  >= 6h  → run rem gates on candidate entries
elapsed_since_last_deep >= 12h → run deep gates on candidate entries
elapsed_since_last_core >= 24h → run core gates on candidate entries
```

Multiple modes can fire in a single cycle (e.g., at 3 AM, all three may be due). Entries are deduplicated — if an entry passes `rem` gates, it is not re-processed by `core` in the same cycle.

### How Modes Stack

`rem` catches hot items fast. `deep` catches warm items at medium frequency. `core` catches everything else daily. Together they form a consolidation pipeline where the most important memories reach long-term storage fastest.

Entries that fail all gates remain in daily logs and will be re-evaluated on the next cycle. They are NOT deleted — they simply haven't qualified yet.

## Configuration

### autodream.json

Location: `~/.openclaw/autodream/autodream.json`

```json
{
  "version": "4.1",
  "profile": "personal-assistant",
  "activeModes": ["core", "rem", "deep"],
  "notificationLevel": "summary",
  "instanceName": "default",
  "timezone": "Asia/Manila",
  "modes": {
    "off":  { "enabled": false },
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

Field reference:

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Config schema version |
| `profile` | string | Selected setup profile (`"personal-assistant"` or `"business-employee"`) |
| `activeModes` | string[] | Which modes are enabled for the cron dispatch |
| `notificationLevel` | string | `"silent"`, `"summary"`, or `"full"` |
| `instanceName` | string | Human-readable instance identifier |
| `timezone` | string | IANA timezone for cron scheduling |
| `modes` | object | Per-mode gate thresholds (user-tunable) |
| `modes.{name}.uniqueMode` | string | How `minUnique` is evaluated: `"day_or_session"` (default), `"day"`, `"session"`, `"channel"`, `"max"` |
| `modes.{name}.fastPathMinScore` | number | Minimum importance for fast-path bypass |
| `modes.{name}.fastPathMinRecallCount` | number | Minimum recall count for fast-path bypass |
| `modes.{name}.fastPathMarkers` | string[] | Markers that trigger fast-path evaluation |
| `lastRun` | object | ISO timestamps of last completed run per mode |

### Changing Modes

Agent can update `autodream.json` on user request:

| Command | Action |
|---------|--------|
| "Set dream mode to core only" | Set `activeModes: ["core"]`, disable rem/deep |
| "Enable all dream modes" | Set `activeModes: ["core", "rem", "deep"]` |
| "Disable dreaming" | Set `activeModes: []` or set all modes `enabled: false` |
| "Lower rem threshold to 0.80" | Update `modes.rem.minScore` to 0.80 |

Always confirm changes with user before writing to conf.

## Preconditions

This skill assumes:
- `~/.openclaw/autodream/autodream.json` exists with a selected profile
- required memory files are initialized
- the recurring isolated cron job is already installed

For first-time installation and bootstrap, read `SETUP.md`.

## Dream Cycle Flow

Each dream runs in an isolated session (see `runtime/auto-dream-prompt.md`):

### Step 0: Load Config + Mode Dispatch
Read `~/.openclaw/autodream/autodream.json`. Check `lastRun` timestamps against current time. Determine which modes are due. If no modes are due, go to Step 0-B (Skip With Recall).

### Step 0-B: Smart Skip + Recall
Check if any unconsolidated daily logs exist in the last 7 days. All processed and no modes due → surface an old memory ("N days ago, you decided...") and show streak count. Never send a blank "nothing to do" message.

### Step 0.5: Snapshot BEFORE
Count LTMEMORY.md lines, decisions, lessons, open threads, total entries.

### Step 1: Collect
Read unconsolidated daily logs. Extract decisions, facts, progress, lessons, and todos.

### Step 1.5: Score + Quality Gate
For each extracted entry, compute preliminary importance score. Look up `referenceCount`, `uniqueSessionCount`, and `uniqueDayCount` from `memory/index.json` (for existing entries) or initialize to current values (for new entries). Apply the gates for each due mode:

```
FOR each due mode (rem first, then deep, then core):
  FOR each candidate entry not yet promoted this cycle:
    IF entry.marker == PERMANENT:
      → MARK entry as QUALIFIED (hard bypass)

    ELSE IF fast-path passes (marker match OR score+recall meet fastPath thresholds):
      → MARK entry as QUALIFIED (fast-path bypass)

    ELSE:
      resolve effective_unique using uniqueMode:
        day_or_session → prefer uniqueDayCount, fall back to uniqueSessionCount
        day            → use uniqueDayCount
        session        → use uniqueSessionCount
        channel        → use uniqueChannelCount
        max            → use highest of all three

      IF entry.importance >= mode.minScore
         AND entry.referenceCount >= mode.minRecallCount
         AND effective_unique >= mode.minUnique:
        → MARK entry as QUALIFIED (regular gate pass)
```

Entries qualified by a stricter mode (rem) are not re-evaluated by a looser mode (core).

### Step 2: Consolidate
Only QUALIFIED entries proceed. Compare with LTMEMORY.md → append new, update existing, skip duplicates. Write workflow preferences to procedures.md. Mark processed daily logs with `<!-- consolidated -->` only when ALL extractable entries from that log have been either qualified or are below all mode thresholds.

### Step 2.5: Snapshot AFTER
Count the same metrics again after changes. Calculate deltas.

### Step 2.8: Stale Thread Detection
Scan Open Threads for items stale >14 days. Include top 3 in notification with context.

### Step 3: Generate Report + Auto-Refresh Dashboard
Append to .dream-log.md with mode info, gate results, change list, insights, and suggestions. If dashboard.html exists, regenerate with latest data.

### Step 4: Notify with Growth Metrics
Send a consolidation report showing:
- Which modes fired this cycle
- Gate results (e.g., "5/12 entries passed rem gates")
- Before → after comparison (entries, decisions, lessons)
- Cumulative growth ("142 → 145 entries, +2.1%")
- Dream streak count ("Dream #14")
- Deferred entries count (entries that didn't pass any gate)
- Milestones when hit
- Top 3 stale reminders (if any)
- Weekly summary on Sundays

### Notification Principles
1. **Every notification must deliver value** — never send empty "nothing happened" messages
2. **Show growth, not just changes** — cumulative stats show the system evolving
3. **Surface forgotten context** — stale thread reminders and old memory recalls
4. **Show gate activity** — user sees which mode promoted which entries
5. **Celebrate milestones** — streak counts and entry milestones build habit

## Manual Triggers

| Command | Action |
|---------|--------|
| "Consolidate memory" / "Dream now" | Run full dream cycle (all modes) in current session |
| "Dream core" / "Dream rem" / "Dream deep" | Run specific mode only |
| "Memory dashboard" | Generate memory/dashboard.html |
| "Export memory" | Export memory/export-YYYY-MM-DD.json |
| "Show dream config" | Display current autodream.json |
| "Set dream mode to core only" | Update autodream.json |

## Language Rules

All output uses the user's preferred language as recorded in USER.md.

## Safety Rules

1. **Never delete daily logs** — only mark with `<!-- consolidated -->`
2. **Never remove ⚠️ PERMANENT items** — user-protected markers
3. **Backup before major changes** — if LTMEMORY.md changes >30%, save .bak first
4. **Config backup** — backup autodream.json → autodream.json.bak before mode changes
5. **Index backup** — backup index.json → index.json.bak before each dream
6. **Sensitive data policy** — only consolidate sensitive info already present in LTMEMORY.md
7. **Deferred entries are safe** — entries that fail gates stay in daily logs, never deleted

## Deterministic Scripts

All arithmetic, threshold checks, date math, and graph algorithms are offloaded to Python scripts. The LLM orchestrates — calling scripts, reading their JSON output, then making judgment calls where needed.

### Script Inventory

| Script | Purpose | When Called |
|--------|---------|-------------|
| `scripts/dispatch.py` | Mode dispatch — which modes are due based on `lastRun` timestamps | Step 0 |
| `scripts/scan.py` | Find unconsolidated daily logs in the scan window | Step 0-A |
| `scripts/snapshot.py` | Count before/after metrics for LTMEMORY.md state | Step 0.5, Step 2.5 |
| `scripts/score.py` | Compute importance scores using exact formula | Step 1.5 |
| `scripts/gate.py` | Apply quality gate thresholds, return qualified/deferred | Step 1.5 |
| `scripts/index.py` | Index CRUD — add entries, assign IDs, update sessions, archive | Step 2, Step 3 |
| `scripts/health.py` | Compute 5-metric health score with BFS reachability | Step 3 |
| `scripts/stale.py` | Detect stale Open Threads with exact day counts | Step 2.8 |

### What stays LLM-driven

| Operation | Why |
|-----------|-----|
| Extract insights from daily logs | Understanding meaning, not text |
| Semantic deduplication | "Set price to ₱5K" = "pricing at five thousand pesos" |
| Route to correct memory layer | Procedural? Episodic? Long-term? Requires judgment |
| Relation linking | Which entries are semantically connected |
| Insight generation | Pattern recognition across the full corpus |
| Report / notification writing | Natural language composition |

### Hybrid Dream Cycle Flow

```
CRON FIRES (4x daily: 4:30/10:30/16:30/22:30)
       │
       ▼
  scripts/dispatch.py            ← Python: which modes are due?
       │
       ▼
  scripts/scan.py                ← Python: which daily logs need processing?
       │
       ▼
  scripts/snapshot.py --save before  ← Python: count before-state
       │
       ▼
  LLM: Read logs, extract entries    ← LLM: understand content, classify
       │
       ▼
  LLM: Write candidates.json        ← LLM: structured output of extracted entries
       │
       ▼
  scripts/score.py               ← Python: compute importance for each entry
       │
       ▼
  scripts/gate.py                ← Python: apply mode thresholds → qualified/deferred
       │
       ▼
  LLM: Semantic dedup + route    ← LLM: compare meanings, decide destinations
       │
       ▼
  scripts/index.py               ← Python: assign IDs, update sessions
       │
       ▼
  LLM: Write to LTMEMORY.md        ← LLM: compose entry text, update sections
       │
       ▼
  scripts/stale.py               ← Python: detect stale threads
       │
       ▼
  scripts/health.py              ← Python: 5-metric health + BFS reachability
       │
       ▼
  scripts/snapshot.py --delta    ← Python: compute before/after deltas
       │
       ▼
  LLM: Generate insights         ← LLM: cross-memory pattern detection
       │
       ▼
  LLM: Write report + notify     ← LLM: compose dream report
       │
       ▼
  scripts/dispatch.py --update   ← Python: write lastRun timestamps
```

## Runtime Prompts

- `runtime/auto-dream-prompt.md` — Recurring cron executor (compact prompt with mode dispatch)
- `runtime/first-dream-prompt.md` — First Dream: post-install full scan (bypasses gates)
- `runtime/dream-prompt.md` — Full prompt (for manual deep consolidation)

## Reference Files

- `references/scoring.md` — Importance scoring, quality gates, forgetting curve, health score algorithms
- `references/memory-template.md` — File templates (autodream.json, LTMEMORY.md, index.json, etc.)
- `references/dashboard-template.html` — HTML dashboard template