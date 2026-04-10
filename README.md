# OpenClaw Auto-Dream v4.1.0

Cognitive memory architecture for OpenClaw agents. Multi-mode dream cycles consolidate daily logs into structured long-term memory with quality gates, importance scoring, forgetting curves, knowledge graphs, and health monitoring.

---
This repository is a fork of [MyClaw.ai - openclaw-auto-dream](https://github.com/LeoYeAI/openclaw-auto-dream)

---

## The Problem

AI agents forget. Session ends, context gone. Files pile up. Daily logs accumulate but remain unsorted, unscored, and disconnected. The agent has data but can't reason about it across time.

Auto-Dream runs periodic "dream cycles" that scan, extract, score, gate, and consolidate the agent's knowledge — automatically and safely.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ┌──────────┐   ┌───────────┐   ┌─────────────┐   ┌────────────┐    │
│   │  COLLECT │──▶│   SCORE   │──▶│ CONSOLIDATE │──▶│  EVALUATE  │    │
│   │          │   │ + GATE    │   │             │   │            │    │
│   │ Scan logs│   │ Importance│   │ Route layers│   │ Health     │    │
│   │ Extract  │   │ Recall cnt│   │ Semantic    │   │ Forgetting │    │
│   │ insights │   │ Unique cnt│   │ dedup + IDs │   │ Insights   │    │
│   └──────────┘   └───────────┘   └─────────────┘   └────────────┘    │
│                                                                      │
│              ☽ Dream Cycle — Mode Dispatch (rem/deep/core) ☾         │
└──────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
     │ 📊 Dashboard │ │ 🔔 Notify   │ │ 📝 Dream Log │
     │HTML + Charts │ │ Push to chat│ │ Append report│
     └──────────────┘ └─────────────┘ └──────────────┘
```

### Dream Modes

Four modes control consolidation frequency and quality gates. Two setup profiles generate different threshold presets — see `profiles/` for details.

Default thresholds shown below are for the **personal-assistant** profile:

| Mode | Cadence | minScore | minRecallCount | minUnique | Purpose |
|------|---------|----------|----------------|-----------|---------|
| `off` | Disabled | — | — | — | No dreaming |
| `core` | Daily 3 AM | 0.72 | 2 | 1 | Daily sweep |
| `rem` | Every 6 hours | 0.85 | 2 | 2 | Fast-track high-signal |
| `deep` | Every 12 hours | 0.80 | 2 | 2 | Mid-frequency warm entries |

A single cron fires 4 times daily (4:30, 10:30, 16:30, 22:30) and dispatches whichever modes are due based on elapsed time. `rem` catches hot items fast, `deep` catches warm items, `core` sweeps everything else daily. Entries that fail all gates remain in daily logs for re-evaluation.

### Quality Gates

An entry must pass **all three gates** for its mode:
- **minScore** — computed importance (`base_weight × recency × reference_boost / 8.0`)
- **minRecallCount** — total times referenced across any context
- **minUnique** — uniqueness count, evaluated according to `uniqueMode` (default: `day_or_session` — prefers day count when available, falls back to session count)

Additional gate features:
- **PERMANENT bypass** — entries marked `⚠️ PERMANENT` always bypass all gates
- **Fast-path bypass** — entries with specific markers (e.g. `HIGH`, `PIN`, `PREFERENCE`, `ROUTINE`, `PROCEDURE`) can bypass regular gates if they meet the softer `fastPathMinScore` and `fastPathMinRecallCount` thresholds. Active markers vary by profile.

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

## Directory Layout

```
auto-dream/                          # Skill root (install location varies)
├── SKILL.md                         # Runtime contract
├── SETUP.md                         # Agent first-time setup guide
├── README.md                        # This file
├── LICENSE
├── runtime/
│   ├── auto-dream-prompt.md         # Recurring cron executor
│   ├── first-dream-prompt.md        # One-time bootstrap (bypasses gates)
│   └── dream-prompt.md              # Full prompt (manual deep consolidation)
├── references/
│   ├── scoring.md                   # Algorithm documentation
│   ├── memory-template.md           # File/JSON templates
│   └── dashboard-template.html      # HTML dashboard template
├── profiles/
│   ├── personal-assistant.md        # Personal wing taxonomy
│   └── business-employee.md         # Business wing taxonomy
└── scripts/
    ├── dispatch.py, scan.py, snapshot.py, score.py
    ├── gate.py, index.py, health.py, stale.py
```

> **Note:** The skill can be installed anywhere under the workspace skill tree. Prompts resolve their own location at runtime. No hardcoded skill path is assumed.

## Install

```bash
git clone https://github.com/catx0rr/Auto-Dream.git \
  ~/.openclaw/workspace/skills/auto-dream
```

The exact install location may vary. Prompts resolve their own location at runtime.

## Setup

Tell the agent: **"Set up Auto-Dream. Read `SETUP.md` in the auto-dream skill directory."**

The agent will:
1. Ask which profile to use (`personal-assistant` or `business-employee`) — or read `AUTODREAM_PROFILE` env var for non-interactive setup
2. Create `~/.openclaw/autodream/autodream.json` with profile-specific mode settings
3. Create a single cron job (4x daily, mode dispatch inside the prompt)
4. Ask your preferred notification level
5. Run the first dream cycle (bypasses quality gates to bootstrap memory)

Home-automation assistants use the `personal-assistant` profile by default.

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
> **Fork note:** This is a fork of [*myclaw.ai - openclaw-auto-dream*](https://github.com/LeoYeAI/openclaw-auto-dream)
> This version redirects Auto-Dream's long-term layer from `MEMORY.md` to `LTMEMORY.md`.
> `MEMORY.md` remains owned by OpenClaw's native `memory-core` and dreaming system.
> Both systems read from the same daily logs but write to separate files — zero overlap.

## License

[MIT](LICENSE)
