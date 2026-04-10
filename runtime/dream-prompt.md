# Auto-Dream Cycle — Execution Prompt (v4.0)

You are running an automatic memory consolidation cycle ("dream"). Execute all phases below precisely and in order.
This file lives inside `runtime/`. Resolve the absolute path of the parent of `runtime/` and use it as `SKILL_ROOT`.

**Language:** All user-facing output (dream reports, notifications, insights, suggestions) MUST use the user's preferred language from `USER.md`. Read `USER.md` first to determine the language. Do NOT default to English.

## Pre-flight

1. Back up `memory/index.json` to `memory/index.json.bak` (if it exists)
2. Read `~/.openclaw/autodream/autodream.json`
3. Read the last entry of `memory/.dream-log.md` (if it exists) for context on what was done last time
4. Note the current UTC timestamp for this dream cycle
5. Read `notificationLevel` from `autodream.json` (default: `"summary"` if absent)

### Mode Dispatch

```
NOW = current UTC timestamp

DUE_MODES = []
FOR each mode in conf.activeModes:
  IF conf.modes[mode].enabled == true:
    elapsed = NOW - conf.lastRun[mode] (treat null as "never run")
    IF mode == "rem"  AND elapsed >= 5.5h  → add "rem" to DUE_MODES
    IF mode == "deep" AND elapsed >= 12h → add "deep" to DUE_MODES
    IF mode == "core" AND elapsed >= 24h → add "core" to DUE_MODES
```

If DUE_MODES is empty AND no unconsolidated logs exist → skip with recall message (see runtime/auto-dream-prompt.md Step 0-B). End session.

If this is a manual trigger ("Dream now"), run all active modes regardless of elapsed time.

---

## Phase 1: Collect

### 1.1 Scan daily logs

List all `memory/YYYY-MM-DD.md` files. Identify files from the **last 7 days** that do NOT end with `<!-- consolidated -->`.

### 1.2 Read unconsolidated files

Read each unconsolidated daily file in full.

### 1.3 Identify priority markers

While reading, flag entries containing any of these markers for priority processing:
- `<!-- important -->` — user-flagged important entries
- `⚠️` — permanent or high-priority content
- `🔥 HIGH` — high-importance entries
- `📌 PIN` — pinned entries

### 1.4 Extract insights

From each file, extract items in these categories:

| Category | Examples |
|----------|---------|
| **Decisions** | Choices made, commitments, direction changes |
| **People** | New contacts, relationship updates, preferences learned about others |
| **Facts** | User preferences, technical details, account info |
| **Projects** | Progress, blockers, completions, milestones |
| **Lessons** | Mistakes, insights, things that worked or failed |
| **Procedures** | Workflows learned, tool usage patterns, communication preferences |
| **Open threads** | Unresolved tasks, pending items |

**Skip**: routine greetings, small talk, transient debug output, information that already exists unchanged in LTMEMORY.md.

Track the source daily log filename for each extracted entry (serves as session ID for `uniqueSessionCount` and day source for `uniqueDayCount` tracking).

---

## Phase 1.5: Score + Quality Gate

### 1.5.1 Compute preliminary importance

For each extracted entry, compute importance score:

```
base_weight = 2.0 if "🔥 HIGH", 1.0 otherwise (⚠️ PERMANENT always final 1.0)
recency = max(0.1, 1.0 - (days_since_last_reference / 180))
ref_boost = max(1.0, log2(referenceCount + 1))
importance = clamp((base_weight × recency × ref_boost) / 8.0, 0.0, 1.0)
```

### 1.5.2 Look up session and day tracking

For each entry, check `memory/index.json`:
- If entry exists in index: read `referenceCount`, `uniqueSessionCount`, `uniqueDayCount`, `sessionSources`, `uniqueDaySources`
  - Increment `referenceCount`
  - If current source log is NOT in `sessionSources`: increment `uniqueSessionCount`, append source log
  - Extract day (YYYY-MM-DD) from source log path. If day is NOT in `uniqueDaySources`: increment `uniqueDayCount`, append day
- If entry is new: initialize `referenceCount = 1`, `uniqueSessionCount = 1`, `sessionSources = [current_log]`, derive day from source, set `uniqueDayCount = 1`, `uniqueDaySources = [day]`

### 1.5.3 Apply quality gates

```
QUALIFIED = []
DEFERRED = []

Sort DUE_MODES by strictness: rem → deep → core

FOR each mode in DUE_MODES (strictest first):
  gate = conf.modes[mode]
  FOR each candidate NOT already in QUALIFIED:
    IF "⚠️ PERMANENT" in entry.markers:
      → add to QUALIFIED with promotedBy = mode (hard bypass)

    ELIF fast-path passes:
      (marker in gate.fastPathMarkers OR
       importance >= gate.fastPathMinScore AND referenceCount >= gate.fastPathMinRecallCount)
      → add to QUALIFIED with promotedBy = mode (fast-path bypass)

    ELSE:
      Resolve effective_unique via gate.uniqueMode:
        day_or_session → prefer uniqueDayCount if > 0, else uniqueSessionCount
        day            → uniqueDayCount
        session        → uniqueSessionCount
        channel        → uniqueChannelCount
        max            → highest of all three

      IF entry.importance >= gate.minScore
         AND entry.referenceCount >= gate.minRecallCount
         AND effective_unique >= gate.minUnique:
        → add to QUALIFIED with promotedBy = mode

Remaining candidates → DEFERRED
```

Record: QUALIFIED_COUNT, DEFERRED_COUNT, per-mode breakdown.

---

## Phase 2: Consolidate

**Only QUALIFIED entries proceed to consolidation.**

### 2.1 Read current memory files

Read these files:
- `LTMEMORY.md`
- `memory/procedures.md` (create from template if missing)
- `memory/index.json` (create from template if missing)
- List `memory/episodes/` directory

### 2.2 Route each qualified item

For each qualified entry, decide its destination:

```
IF item is a "how-to", preference, workflow, or tool pattern:
    → append/update in memory/procedures.md under matching section

ELIF item is part of a multi-event project narrative or significant event arc:
    → append to memory/episodes/<project-name>.md
    → create the episode file if it doesn't exist (use episode template)

ELSE (decisions, facts, people, milestones, lessons, open threads):
    → append/update in LTMEMORY.md under matching section
```

### 2.3 Semantic deduplication

Before writing any item, check if a semantically equivalent entry already exists:
- Compare **meaning**, not exact text
- If duplicate found: keep the better-worded, more complete version
- If existing entry needs updating (e.g., status changed): update in-place

### 2.4 Assign entry IDs

Every new entry gets a unique ID in format `mem_NNN`:
- Read current max ID from `memory/index.json` entries
- Increment for each new entry
- Record the ID as a comment next to the entry: `<!-- mem_NNN -->`

### 2.5 Link relations

When entries are related to each other:
- Record `related: [mem_xxx, mem_yyy]` in the index entry
- Examples: a decision that affects a project, a lesson learned from a mistake

### 2.6 Write changes

1. Write updated `LTMEMORY.md` (update `_Last updated:_` line)
2. Write updated `memory/procedures.md` (update `_Last updated:_` line)
3. Write any new/updated episode files
4. **Safety check**: if LTMEMORY.md changes by more than 30% in size, create `memory/LTMEMORY.md.bak` before writing

### 2.7 Mark processed files

A daily log file gets `<!-- consolidated -->` only when ALL of these are true:
- Every extractable entry from that log is either QUALIFIED or has been DEFERRED with importance below the lowest active mode's minScore
- OR the file has been scanned for 7+ consecutive cycles with no new qualifications

This prevents premature marking that would hide entries from future cycles.

---

## Phase 3: Evaluate

### 3.1 Build index entries

For each memory entry (in LTMEMORY.md, procedures.md, and episodes), ensure an entry exists in `memory/index.json`:

```json
{
  "id": "mem_NNN",
  "summary": "Brief one-line summary",
  "source": "memory/YYYY-MM-DD.md",
  "target": "LTMEMORY.md#section-name",
  "created": "YYYY-MM-DD",
  "lastReferenced": "YYYY-MM-DD",
  "referenceCount": 7,
  "uniqueSessionCount": 4,
  "sessionSources": ["memory/2026-04-01.md", "memory/2026-04-03.md", "memory/2026-04-04.md", "memory/2026-04-05.md"],
  "uniqueDayCount": 4,
  "uniqueDaySources": ["2026-04-01", "2026-04-03", "2026-04-04", "2026-04-05"],
  "promotedBy": "rem",
  "importance": 0.82,
  "tags": ["tag1", "tag2"],
  "related": ["mem_xxx"]
}
```

### 3.2 Re-score importance (post-consolidation)

Re-calculate importance for all entries (including previously consolidated ones) using the full formula from `references/scoring.md`. This ensures the health metrics reflect the true state after this cycle's changes.

### 3.3 Apply forgetting curve

For entries where ALL conditions are true:
- `lastReferenced` is >90 days ago
- `importance` < 0.3
- NOT marked `⚠️ PERMANENT` or `📌 PIN`

Action:
1. Compress the entry to a one-line summary
2. Append the summary to `memory/.archive.md` with original ID and date
3. Remove the full entry from its source file (LTMEMORY.md or procedures.md)
4. Mark the index entry with `"archived": true`

**Never archive entries from episode files** — episodes are append-only.

### 3.4 Calculate health score

Using the 5-metric formula (see `references/scoring.md` for full details):

```
health = (freshness×0.25 + coverage×0.25 + coherence×0.2 + efficiency×0.15 + reachability×0.15) × 100
```

Scale to 0–100 and round to integer.

### 3.5 Update index stats

```json
{
  "stats": {
    "totalEntries": "<count>",
    "avgImportance": "<mean of all importance scores>",
    "lastPruned": "<ISO timestamp or null>",
    "healthScore": "<0-100>",
    "healthMetrics": {
      "freshness": "<0.0-1.0>",
      "coverage": "<0.0-1.0>",
      "coherence": "<0.0-1.0>",
      "efficiency": "<0.0-1.0>",
      "reachability": "<0.0-1.0>"
    },
    "insights": ["<insight text>", "..."],
    "gateStats": {
      "lastCycleQualified": "<count>",
      "lastCycleDeferred": "<count>",
      "lastCycleBreakdown": { "rem": "<count>", "deep": "<count>", "core": "<count>" }
    }
  }
}
```

Append a health history snapshot to `stats.healthHistory`:
```json
{ "date": "YYYY-MM-DD", "score": 82 }
```

Trim `healthHistory` to the most recent 90 entries.

### 3.6 Update autodream.json

Write `lastRun` timestamps for each mode that fired this cycle:

```json
"lastRun": {
  "core": "2026-04-05T03:00:00Z",
  "rem": "2026-04-05T06:00:00Z",
  "deep": "2026-04-05T00:00:00Z"
}
```

Back up `autodream.json` → `autodream.json.bak` before writing.

### 3.7 Generate dream report

Append to `memory/.dream-log.md`:

```markdown
## 🌀 Dream Report — YYYY-MM-DD HH:MM UTC

### ⚙️ Mode Dispatch
- Modes fired: {list}
- Gate results: {QUALIFIED_COUNT}/{TOTAL_CANDIDATES} qualified
  - rem: {n} | deep: {n} | core: {n}
- Deferred: {DEFERRED_COUNT} entries

### 📊 Stats
- Scanned: N files | New: N | Updated: N | Pruned: N
- LTMEMORY.md: N lines | Episodes: N | Procedures: N entries

### 🧠 Health: XX/100
- Freshness: XX% | Coverage: XX% | Coherence: XX% | Efficiency: XX% | Reachability: XX%

### 🔮 Insights
- [Pattern] <non-obvious observation with supporting evidence>
- [Trend] <pattern detected across time or multiple entries>
- [Gap] <missing knowledge area worth addressing>

### 📝 Changes
- [New] (via {mode}) <brief description>
- [Updated] (via {mode}) <brief description>
- [Archived] <brief description>

### 💡 Suggestions
- <actionable suggestions based on health scores, insights, and gate stats>
```

### 3.8 Generate Insights

Review the full memory graph, recent changes, health history, and cross-layer patterns. Generate **1–3 non-obvious insights**.

Types of insights to look for:

- **Pattern connections**: Similarities across different projects or time periods.
- **Temporal patterns**: Decision clustering, planning rhythms detected from created/lastReferenced dates.
- **Gap detection**: Conspicuously absent knowledge domains.
- **Trend alerts**: Multi-cycle health degradation from `healthHistory`.
- **Relationship density**: Entries with many inbound but no outbound relations.
- **Gate patterns**: Entries repeatedly deferred across cycles — may need marker promotion or threshold adjustment.

Populate `stats.insights` in index.json with plain-text insight strings.

---

## Post-flight: Notification

Based on `notificationLevel` from `autodream.json`:

### If `silent`:
Skip. Dream report written to `memory/.dream-log.md`. End session.

### If `summary`:
```
🌀 Dream complete ({modes_fired}) — Health: XX/100
📥 Qualified: {Q}/{T} | rem: {n} · deep: {n} · core: {n} | Deferred: {D}
🔮 Insight: [top insight]
💡 Tip: [top suggestion]
```

### If `full`:
Reply with the complete dream report. If very long, prioritize: Mode Dispatch + Stats + Health + Insights + top 3 Changes + top 2 Suggestions.

---

## Post-flight: Dashboard

If `memory/dashboard.html` exists, regenerate with latest data.

---

## Post-flight: Final Reply

Reply with:
- Which modes fired and gate results
- What was collected, qualified, and consolidated
- Current health score and component breakdown
- Top insight (1 sentence)
- Count of deferred entries
- Any blocking suggestions
