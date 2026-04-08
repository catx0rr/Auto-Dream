# Scoring, Quality Gates & Forgetting — Memory Evaluation Algorithms (v4.0)

## Importance Score

Every memory entry receives an importance score on each dream cycle.

### Formula

```
importance = clamp(base_weight × recency_factor × reference_boost, 0.0, 1.0)
```

### Components

#### base_weight

Default weight determined by user markers:

| Marker | base_weight | Notes |
|--------|-------------|-------|
| (none) | 1.0 | Default |
| `🔥 HIGH` | 2.0 | Doubles importance |
| `📌 PIN` | 1.0 | Normal weight but exempt from archival |
| `⚠️ PERMANENT` | — | Always 1.0 final score, skip formula. Also bypasses quality gates. |

#### recency_factor

How recently the entry was referenced or updated:

```
days_elapsed = today - lastReferenced
recency_factor = max(0.1, 1.0 - (days_elapsed / 180))
```

Characteristics:
- Referenced today: `1.0`
- Referenced 30 days ago: `0.83`
- Referenced 90 days ago: `0.5`
- Referenced 180+ days ago: `0.1` (floor)

#### reference_boost

How many other entries or sessions have referenced this entry:

```
reference_boost = max(1.0, log2(referenceCount + 1))
```

Examples:
- `referenceCount = 0` → `max(1.0, log2(1)) = 1.0`
- `referenceCount = 1` → `max(1.0, log2(2)) = 1.0`
- `referenceCount = 7` → `log2(8) = 3.0`
- `referenceCount = 15` → `log2(16) = 4.0`

### Full pseudocode

```python
def compute_importance(entry, today):
    # Permanent entries always score 1.0
    if "⚠️ PERMANENT" in entry.markers:
        return 1.0

    # Base weight from markers
    base = 2.0 if "🔥 HIGH" in entry.markers else 1.0

    # Recency decay
    days = (today - entry.lastReferenced).days
    recency = max(0.1, 1.0 - (days / 180))

    # Reference boost (logarithmic, floored at 1.0)
    ref_boost = max(1.0, log2(entry.referenceCount + 1))

    # Combine and normalize
    # Max realistic: 2.0 * 1.0 * 4.0 = 8.0
    raw = base * recency * ref_boost
    normalized = raw / 8.0
    return min(1.0, max(0.0, normalized))
```

---

## Quality Gates (v4.0)

Quality gates determine whether an extracted entry qualifies for consolidation into long-term memory. Each dream mode defines three thresholds that an entry must **all** pass.

### Gate Parameters

| Parameter | Field in index.json | What it measures |
|-----------|-------------------|------------------|
| `minScore` | `importance` | Computed importance score (0.0–1.0) |
| `minRecallCount` | `referenceCount` | Total times this entry has been referenced |
| `minUnique` | `uniqueSessionCount` | Distinct sessions that have referenced this entry |

### Mode Thresholds

Defined in `~/.openclaw/autodream/autodream.json`:

| Mode | minScore | minRecallCount | minUnique |
|------|----------|----------------|-----------|
| `core` | 0.75 | 3 | 2 |
| `rem` | 0.85 | 4 | 3 |
| `deep` | 0.80 | 3 | 3 |

### Gate Evaluation Order

Gates are evaluated **strictest mode first** (rem → deep → core). Once an entry is qualified by any mode, it is not re-evaluated by subsequent modes.

```python
def apply_gates(candidates, due_modes, conf):
    qualified = []
    deferred = []

    # Sort modes by strictness (highest minScore first)
    mode_order = sorted(due_modes, key=lambda m: conf.modes[m].minScore, reverse=True)

    for mode in mode_order:
        gate = conf.modes[mode]
        for entry in candidates:
            if entry in qualified:
                continue  # already promoted by stricter mode

            # PERMANENT always passes
            if "⚠️ PERMANENT" in entry.markers:
                qualified.append((entry, mode))
                continue

            if (entry.importance >= gate.minScore
                and entry.referenceCount >= gate.minRecallCount
                and entry.uniqueSessionCount >= gate.minUnique):
                qualified.append((entry, mode))

    deferred = [e for e in candidates if e not in [q[0] for q in qualified]]
    return qualified, deferred
```

### Gate Bypass Rules

| Condition | Bypass? | Rationale |
|-----------|---------|-----------|
| `⚠️ PERMANENT` marker | Yes | User-protected entries always consolidate |
| `🔥 HIGH` marker | No | HIGH doubles base_weight but still must pass gates |
| `📌 PIN` marker | No | PIN prevents archival but does not bypass intake gates |
| First Dream (post-install) | Yes | Bootstrap run consolidates everything to seed memory |
| Manual trigger ("Dream now") | Configurable | Can run with or without gates per user preference |

---

## Unique Session Count — Tracking `uniqueSessionCount`

### Purpose

`referenceCount` tracks total references but can be inflated by a single long conversation mentioning the same topic repeatedly. `uniqueSessionCount` ensures an entry has been referenced across **distinct sessions**, providing a cross-session relevance signal.

### Definition

A "session" is identified by the daily log filename (`memory/YYYY-MM-DD.md`). Each daily log represents one session boundary.

### Tracking Algorithm

```python
def update_session_tracking(entry, source_log_filename, index):
    """Called during the Collect phase for each extracted entry."""

    if entry.id not in index.entries:
        # New entry — initialize
        entry.referenceCount = 1
        entry.uniqueSessionCount = 1
        entry.sessionSources = [source_log_filename]
        return

    existing = index.entries[entry.id]

    # Always increment referenceCount
    existing.referenceCount += 1

    # Only increment uniqueSessionCount if this is a new session
    if source_log_filename not in existing.sessionSources:
        existing.uniqueSessionCount += 1
        existing.sessionSources.append(source_log_filename)

    existing.lastReferenced = today
```

### Index Entry Schema (v3.1)

The `sessionSources` field is stored in `index.json` but kept compact — only the last 30 session filenames are retained (older ones are trimmed from the front since `uniqueSessionCount` already captured the count).

```json
{
  "id": "mem_001",
  "summary": "One-line summary",
  "source": "memory/2026-04-01.md",
  "target": "LTMEMORY.md#projects",
  "created": "2026-04-01",
  "lastReferenced": "2026-04-05",
  "referenceCount": 7,
  "uniqueSessionCount": 4,
  "sessionSources": ["memory/2026-04-01.md", "memory/2026-04-02.md", "memory/2026-04-04.md", "memory/2026-04-05.md"],
  "importance": 0.82,
  "tags": ["project", "architecture"],
  "related": ["mem_002", "mem_005"],
  "archived": false
}
```

### Edge Cases

| Case | Behavior |
|------|----------|
| Same entry mentioned 5 times in one daily log | `referenceCount += 5`, `uniqueSessionCount += 1` |
| Entry referenced in 3 different daily logs | `uniqueSessionCount = 3` (one per log) |
| Entry exists in index but never extracted before | Initialize `uniqueSessionCount = 1`, `sessionSources = [current_log]` |
| Manual "Dream now" trigger (no daily log source) | Use `"manual-YYYY-MM-DD"` as synthetic session ID |

---

## Forgetting Curve

Entries that are no longer relevant should be gracefully archived, not deleted.

### Archival conditions

An entry is eligible for archival when **ALL** of these are true:

```
1. days_since_last_referenced > 90
2. importance < 0.3
3. NOT marked ⚠️ PERMANENT
4. NOT marked 📌 PIN
5. NOT in an episode file (episodes are append-only)
```

### Archival process

```
1. Compress entry to one-line summary
2. Append to memory/.archive.md:
   - [mem_NNN] (YYYY-MM-DD) One-line summary
3. Remove full entry from source file (LTMEMORY.md or procedures.md)
4. Set entry.archived = true in index.json
5. Keep the index entry (for relation tracking and reachability graph)
```

### Decay visualization

```
Importance
1.0 │ ████
    │ ████████
    │ ████████████
0.5 │ ████████████████
    │ ████████████████████
0.3 │─────────────────────────── archival threshold
    │ ████████████████████████████
0.1 │ ████████████████████████████████
0.0 └──────────────────────────────────→ Days
    0    30    60    90    120   150   180
```

---

## Health Score (v3.0 — Five Metrics)

The health score measures overall memory system quality on a 0–100 scale.

### Formula

```
health = (freshness×0.25 + coverage×0.25 + coherence×0.2 + efficiency×0.15 + reachability×0.15) × 100
```

### Metric 1: Freshness (weight: 0.25)

What proportion of entries have been recently referenced?

```
freshness = entries_referenced_in_last_30_days / total_entries
```

### Metric 2: Coverage (weight: 0.25)

Are all knowledge categories being actively maintained?

```
categories = [
    "Core Identity", "User", "Projects", "Business",
    "People & Team", "Strategy", "Key Decisions",
    "Lessons Learned", "Environment", "Open Threads"
]
coverage = categories_with_updates_in_last_14_days / len(categories)
```

### Metric 3: Coherence (weight: 0.2)

How well-connected is the memory graph?

```
coherence = entries_with_at_least_one_relation / total_entries
```

### Metric 4: Size Efficiency (weight: 0.15)

Is LTMEMORY.md staying concise and well-pruned?

```
efficiency = max(0.0, 1.0 - (memory_md_line_count / 500))
```

### Metric 5: Reachability (weight: 0.15)

What fraction of the memory graph is mutually reachable via relation links?

#### Algorithm

```python
def compute_reachability(entries):
    if not entries:
        return 0.0

    adj = defaultdict(set)
    ids = {e["id"] for e in entries if not e.get("archived")}

    for entry in entries:
        if entry.get("archived"):
            continue
        for related_id in entry.get("related", []):
            if related_id in ids:
                adj[entry["id"]].add(related_id)
                adj[related_id].add(entry["id"])

    visited = set()
    components = []
    for node in ids:
        if node not in visited:
            component = set()
            queue = [node]
            while queue:
                current = queue.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                queue.extend(adj[current] - visited)
            components.append(len(component))

    total = len(ids)
    if total == 0:
        return 0.0

    weighted_sum = sum(size * size for size in components)
    reachability = weighted_sum / (total * total)
    return min(1.0, reachability)
```

#### Interpretation

| Value | Meaning |
|-------|---------|
| `1.0` | All entries in one connected component — perfect graph |
| `0.7–0.9` | Most entries connected, a few isolated clusters |
| `0.4–0.6` | Significant fragmentation — many topics not linked |
| `0.1–0.3` | Heavily fragmented — knowledge silos |
| `0.0–0.1` | Almost no connections — a flat list, not a graph |

---

## Suggestion Triggers

Generate suggestions in the dream report when:

| Condition | Suggestion |
|-----------|------------|
| `freshness < 0.5` | "Many entries are stale — review for relevance or increase cross-referencing" |
| `coverage < 0.5` | "Several LTMEMORY.md sections haven't been updated — check for knowledge gaps" |
| `coherence < 0.3` | "Low entry connectivity — consider linking related memories manually" |
| `efficiency < 0.3` | "LTMEMORY.md is large (N lines) — review for pruning or archival opportunities" |
| `reachability < 0.4` | "Memory graph is fragmented (N isolated clusters) — add cross-references" |
| `DEFERRED_COUNT > 10` | "Many entries deferred — consider lowering gate thresholds or running in core mode" |
| `no entries pass rem gates for 3+ cycles` | "rem mode is too strict — no entries qualifying. Review minScore threshold" |
| `health declining 3+ cycles` | "Health trending down for N cycles — investigate which metric is deteriorating" |
