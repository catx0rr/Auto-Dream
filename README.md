# OpenClaw Auto-Dream v2.0.0

Cognitive memory architecture for OpenClaw agents. Multi-mode dream cycles consolidate daily logs into structured long-term memory with quality gates, importance scoring, forgetting curves, knowledge graphs, and health monitoring.

---
## This repository is a fork of [MyClaw.ai - openclaw-auto-dream](https://github.com/LeoYeAI/openclaw-auto-dream)

---

## The Problem

AI agents forget. Session ends, context gone. Files pile up. Daily logs accumulate but remain unsorted, unscored, and disconnected. The agent has data but can't reason about it across time.

Auto-Dream runs periodic "dream cycles" that scan, extract, score, gate, and consolidate the agent's knowledge — automatically and safely.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ┌──────────┐   ┌───────────┐   ┌─────────────┐   ┌────────────┐  │
│   │  COLLECT  │──▶│   SCORE   │──▶│ CONSOLIDATE │──▶│  EVALUATE  │  │
│   │          │   │ + GATE    │   │             │   │            │  │
│   │ Scan logs│   │ Importance│   │ Route layers│   │ Health     │  │
│   │ Extract  │   │ Recall cnt│   │ Semantic    │   │ Forgetting │  │
│   │ insights │   │ Unique cnt│   │ dedup + IDs │   │ Insights   │  │
│   └──────────┘   └───────────┘   └─────────────┘   └────────────┘  │
│                                                                      │
│              ☽ Dream Cycle — Mode Dispatch (rem/deep/core) ☾         │
└──────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
     │  📊 Dashboard │ │ 🔔 Notify   │ │ 📝 Dream Log │
     │  HTML + Charts│ │ Push to chat│ │ Append report│
     └──────────────┘ └─────────────┘ └──────────────┘
```

### Dream Modes

Four modes control consolidation frequency and quality gates:

| Mode | Cadence | minScore | minRecallCount | minUnique | Purpose |
|------|---------|----------|----------------|-----------|---------|
| `off` | Disabled | — | — | — | No dreaming |
| `core` | Daily 3 AM | 0.75 | 3 | 2 | Daily sweep |
| `rem` | Every 6 hours | 0.85 | 4 | 3 | Fast-track high-signal |
| `deep` | Every 12 hours | 0.80 | 3 | 3 | Mid-frequency warm entries |

A single cron fires 4 times daily (4:30, 10:30, 16:30, 22:30) and dispatches whichever modes are due based on elapsed time. `rem` catches hot items fast, `deep` catches warm items, `core` sweeps everything else daily. Entries that fail all gates remain in daily logs for re-evaluation.

### Quality Gates

An entry must pass **all three gates** for its mode:
- **minScore** — computed importance (`base_weight × recency × reference_boost / 8.0`)
- **minRecallCount** — total times referenced across any context
- **minUnique** — distinct sessions that referenced it (prevents single-conversation inflation)

### Five Memory Layers

| Layer | Storage | What Goes Here |
|-------|---------|---------------|
| **Working** | LCM plugin (optional) | Real-time context compression & semantic recall |
| **Episodic** | `memory/episodes/*.md` | Project narratives, event timelines, story arcs |
| **Long-term** | `LTMEMORY.md` | Facts, decisions, people, milestones, strategy (Auto-Dream layer) |
| **Procedural** | `memory/procedures.md` | Workflows, preferences, tool patterns, shortcuts |
| **Index** | `memory/index.json` | Metadata, importance scores, relations, health stats |

### Configuration

Mode settings stored at `~/.openclaw/autodream/autodream.json` — user-tunable thresholds, notification level, timezone, and last-run timestamps.

## Features

### Importance Scoring

```
importance = (base_weight × recency_factor × reference_boost) / 8.0
```

- **Recency**: `max(0.1, 1.0 - days/180)` — gradual decay over 6 months
- **References**: `log₂(count + 1)` — logarithmic boost for frequently-referenced entries
- **Markers**: `🔥 HIGH` doubles base weight; `⚠️ PERMANENT` always scores 1.0 and bypasses gates

### Intelligent Forgetting

Memories aren't deleted — they're gracefully archived:
- Entry must be >90 days unreferenced AND importance < 0.3
- Compressed to a one-line summary in `memory/.archive.md`
- `⚠️ PERMANENT` and `📌 PIN` entries are immune

### Knowledge Graph

Entries are linked by semantic relations. Reachability metric measures graph connectivity via union-find algorithm. Detects isolated knowledge clusters and suggests cross-references.

### Health Score (5 Metrics)

```
health = (freshness×0.25 + coverage×0.25 + coherence×0.2 + efficiency×0.15 + reachability×0.15) × 100
```

### Push Notifications

| Level | What You Get |
|-------|-------------|
| `silent` | Nothing — logged to .dream-log.md only |
| `summary` | Compact health + gate results + top insight |
| `full` | Complete dream report with all sections |

### Interactive Dashboard

Zero-dependency HTML dashboard with health gauge, metric cards, memory distribution chart, trend line, and force-directed knowledge graph.

### Cross-Instance Migration

Portable JSON bundle export/import with conflict resolution and pre-import backup.

## Install

```bash
git clone https://github.com/catx0rr/openclaw-auto-dream \
  ~/.openclaw/workspace/skills/auto-dream
```

## Setup

Tell the agent: **"Set up Auto-Dream. Read `~/.openclaw/workspace/skills/auto-dream/SETUP.md"**

The agent will:
1. Create `~/.openclaw/autodream/autodream.json` with default mode settings
2. Create a single cron job (4x daily, mode dispatch inside the prompt)
3. Ask your preferred notification level
4. Run the first dream cycle (bypasses quality gates to bootstrap memory)

### Manual Triggers

- "Dream now" — run all modes immediately
- "Dream core" / "Dream rem" / "Dream deep" — run specific mode
- "Show dream config" — display current autodream.json
- "Set dream mode to core only" — update active modes

## Safety

| Rule | Why |
|------|-----|
| Never delete daily logs | Immutable source of truth |
| Never remove `⚠️ PERMANENT` | User protection is absolute |
| Episodes are append-only | Narrative history preserved forever |
| Auto-backup on >30% change | Prevents accidental corruption |
| Config + index backup every cycle | Always recoverable |
| Deferred entries stay in daily logs | Never deleted, re-evaluated next cycle |

## How It Works Under the Hood

| Primitive | Role |
|-----------|------|
| **Cron** | 4x daily cron (30 4,10,16,22), mode dispatch inside prompt |
| **Isolated Sessions** | Runs consolidation without polluting main chat |
| **File System** | Reads/writes memory files across all five layers |
| **LCM** | Provides working memory compression (optional) |

No external dependencies. No API keys. No databases. Just files and intelligence.

## CREDITS
> This is a fork of [myclaw.ai - openclaw-auto-dream](https://github.com/LeoYeAI/openclaw-auto-dream)
> **Fork note:** This version redirects Auto-Dream's long-term layer from `MEMORY.md` to `LTMEMORY.md`.
> `MEMORY.md` remains owned by OpenClaw's native `memory-core` and dreaming system.
> Both systems read from the same daily logs but write to separate files — zero overlap.

## License

[MIT](LICENSE)
