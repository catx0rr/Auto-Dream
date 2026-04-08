# Auto-Dream Lite — Hybrid Multi-Mode Memory Consolidation

Read USER.md to determine user's language. All output in that language.
Working directory: the workspace root.
Scripts directory: `skills/auto-dream/scripts/`

**Hybrid rule:** Call Python scripts for all arithmetic, thresholds, date math, and counting. Use LLM judgment only for semantic understanding, deduplication, routing, insight generation, and report writing.

---

## Step 0: Mode Dispatch [SCRIPT]

```bash
python3 skills/auto-dream/scripts/dispatch.py --config ~/.openclaw/autodream/autodream.json
```

Read the JSON output:
- `due_modes` → list of modes to run this cycle (with gate thresholds)
- `not_due` → modes not yet due (with `next_due_in`)
- `notification_level` → summary/full/silent

If `due_modes` is empty → go to Step 0-A.

## Step 0-A: Scan for Work [SCRIPT]

```bash
python3 skills/auto-dream/scripts/scan.py --log-dir memory --days 7
```

Read the JSON output:
- `has_work` → true if unconsolidated logs exist
- `unconsolidated` → list of files with dates and sizes

If `has_work == false` AND `due_modes` is empty → go to Step 0-B (Skip With Recall).
If `has_work == true` BUT `due_modes` is empty → go to Step 0-B (still skip — no modes due).
If `due_modes` is not empty → proceed to Step 0.5.

## Step 0-B: Skip With Recall [LLM]

Even when skipping, send a useful message. Scan LTMEMORY.md for Open Threads not marked [x] — find the oldest one with context. Check daily logs from 14+ days ago for matching topics.

```bash
python3 skills/auto-dream/scripts/stale.py --memory-file LTMEMORY.md --index memory/index.json --threshold 14 --top 1
```

Use the stale result to compose the skip message:

```
🌙 No modes due — skipped consolidation

💭 From your memory:
   {N} days ago ({date}), {one-line context from stale result}.
   {Follow-up question if relevant}

📈 Memory: {total_entries} entries · Health {score}/100 · Streak: {N} dreams
⚙️ Active modes: {list} · Next due: {mode} in {time}
```

END here. Do not proceed.

---

## Step 0.5: Snapshot BEFORE [SCRIPT]

```bash
python3 skills/auto-dream/scripts/snapshot.py --memory-file LTMEMORY.md --save-as before
```

Note the saved path (`/tmp/autodream-snapshot-before.json`). Read the dream count from output.

---

## Step 1: Collect [LLM]

Read all unconsolidated daily logs (from Step 0-A file list). Extract:
- Decisions (choices, direction changes)
- Key facts (data updates, account info, technical details)
- Project progress (milestones, blockers, completions)
- Lessons (failures, wins)
- Todos (unfinished items)

Skip small talk and content already in LTMEMORY.md that hasn't changed.

Track the source daily log filename for each entry (serves as session ID).

**Output:** Write extracted entries to `/tmp/autodream-candidates.json` as a JSON array:

```json
[
  {
    "summary": "Decision to set dental clinic pilot pricing at ₱5,000/month",
    "source": "memory/2026-04-05.md",
    "category": "decision",
    "referenceCount": 1,
    "uniqueSessionCount": 1,
    "marker": null,
    "target_section": "Key Decisions"
  }
]
```

For entries that already exist in the index, look up their current `referenceCount` and `uniqueSessionCount` and carry those forward (the score script needs accurate values).

---

## Step 1.5: Score + Gate [SCRIPT]

### Score all candidates:

```bash
python3 skills/auto-dream/scripts/score.py --index memory/index.json --check-archival
```

Merge the importance scores into the candidates file (update each entry's `importance` field).

### Apply quality gates:

```bash
python3 skills/auto-dream/scripts/gate.py \
  --candidates /tmp/autodream-candidates.json \
  --config ~/.openclaw/autodream/autodream.json \
  --modes rem,deep,core
```

(Use the actual due modes from Step 0, comma-separated.)

Read the JSON output:
- `qualified` → entries that passed gates (with `promotedBy` field)
- `deferred` → entries that failed all gates (with `fail_reasons`)
- `breakdown` → count per mode

Record: QUALIFIED_COUNT, DEFERRED_COUNT.

**Only QUALIFIED entries proceed to Step 2.**

---

## Step 2: Consolidate [LLM]

Read LTMEMORY.md, compare qualified entries:
- **New** → append to LTMEMORY.md in the right section
- **Updated** → update in place
- **Duplicate** → skip (semantic dedup — compare meaning, not text)
- **Procedures/preferences** → append to memory/procedures.md

### Assign IDs [SCRIPT]

For each new entry:

```bash
python3 skills/auto-dream/scripts/index.py --index memory/index.json --next-id
```

Use the returned ID. After writing to LTMEMORY.md, add the entry to the index:

```bash
python3 skills/auto-dream/scripts/index.py --index memory/index.json --add /tmp/entry.json
```

### Update session tracking [SCRIPT]

For existing entries that were re-referenced:

```bash
python3 skills/auto-dream/scripts/index.py --index memory/index.json --update-session mem_042 --source memory/2026-04-05.md
```

### Write changes [LLM]

Update `_Last updated:` date in LTMEMORY.md. Write updated procedures.md if needed.

### Mark processed files

A daily log gets `<!-- consolidated -->` only when ALL extractable entries from that log are either QUALIFIED or have been DEFERRED with importance below the lowest active mode's minScore.

---

## Step 2.5: Snapshot AFTER [SCRIPT]

```bash
python3 skills/auto-dream/scripts/snapshot.py --memory-file LTMEMORY.md --save-as after
python3 skills/auto-dream/scripts/snapshot.py --delta /tmp/autodream-snapshot-before.json /tmp/autodream-snapshot-after.json
```

Read the delta output for the notification.

---

## Step 2.8: Stale Thread Detection [SCRIPT]

```bash
python3 skills/auto-dream/scripts/stale.py --memory-file LTMEMORY.md --index memory/index.json --threshold 14 --top 3
```

Read `stale` array for the notification.

---

## Step 3: Health + Evaluation [SCRIPT]

### Compute health score:

```bash
python3 skills/auto-dream/scripts/health.py --index memory/index.json --memory-file LTMEMORY.md
```

Read: `health_score`, `metrics`, `suggestions`, `reachability_detail`.

### Check archival candidates:

```bash
python3 skills/auto-dream/scripts/score.py --index memory/index.json --check-archival
```

For each `archival_candidates` entry, archive via:

```bash
python3 skills/auto-dream/scripts/index.py --index memory/index.json --archive mem_015 --summary "Old API endpoint"
```

Also remove the full entry from LTMEMORY.md and append the one-line summary to `memory/.archive.md`.

### Update index stats:

Write the health and gate results to a temp file, then:

```bash
python3 skills/auto-dream/scripts/index.py --index memory/index.json --update-stats /tmp/autodream-stats.json
```

---

## Step 3.5: Insights [LLM]

Review the health output, gate results, recent changes, and cross-layer patterns. Generate 1–2 non-obvious insights that scripts can't detect (semantic patterns, gap detection, trend interpretation).

---

## Step 3.7: Update Config [SCRIPT]

```bash
python3 skills/auto-dream/scripts/dispatch.py --config ~/.openclaw/autodream/autodream.json --update-lastrun core,rem,deep
```

(Use only the modes that actually fired.)

---

## Step 3.8: Auto-Refresh Dashboard

If memory/dashboard.html exists, regenerate with latest data. Skip if it doesn't exist.

---

## Step 4: Report + Notify [LLM]

Append to memory/.dream-log.md, then compose notification.

### Check for milestones:
- DREAM_COUNT+1 == 1 → "🎉 First dream complete!"
- DREAM_COUNT+1 == 7 → "🏅 One week streak!"
- DREAM_COUNT+1 == 30 → "🏆 One month streak!"
- TOTAL_AFTER crosses 100/200/500 → "📊 Memory milestone!"

### Notification format:

```
🌙 Dream #{N} complete ({modes_fired} cycle)

📥 Qualified: {Q}/{T} entries
   rem: {n} · deep: {n} · core: {n}
   Deferred: {D} (retry next cycle)
📈 Total: {BEFORE} → {AFTER} entries ({pct}% growth)
🧠 Health: {score}/100 — {rating}

🔮 Highlights:
   • {change_1} (via {mode})
   • {change_2} (via {mode})

💡 Insight: {top insight}

⏳ Stale: {stale items if any}

{milestone if any}
💬 Let me know if anything was missed
```

---

## Safety Rules

- Never delete daily log originals
- Never remove ⚠️ PERMANENT entries
- ⚠️ PERMANENT entries bypass quality gates
- Backup: LTMEMORY.md changes >30% → save LTMEMORY.md.bak first
- Backup: autodream.json → autodream.json.bak (handled by dispatch.py)
- Backup: index.json → index.json.bak (handled by index.py)
- Deferred entries remain in daily logs — never deleted, never marked consolidated prematurely

---

## Cleanup

After the dream cycle, remove temp files:

```bash
rm -f /tmp/autodream-candidates.json /tmp/autodream-snapshot-*.json /tmp/autodream-stats.json /tmp/entry.json
```
