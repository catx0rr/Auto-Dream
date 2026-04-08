## Setup

### 0. First Dream (Run Immediately After Install)

After setup is complete, DO NOT wait for the cron schedule. Immediately run the First Dream:

1. Read `references/first-dream-prompt.md`
2. Execute every step in the current session (not isolated — user should see it happen)
3. First Dream bypasses quality gates — consolidates everything to bootstrap the memory

### 1. Initialize Files

Working Directory `~/.openclaw/workspace`

```bash
mkdir -p ~/.openclaw/autodream
mkdir -p memory/episodes
```

Create `autodream.json` from template in `references/memory-template.md` if missing.

Ensure the following files exist (create from `references/memory-template.md` templates if missing):
- `memory/index.json`
- `memory/procedures.md`
- `memory/.dream-log.md`
- `memory/.archive.md`

### 2. Create Cron Job

Single cron at scheduled intervals (30 4,10,16,22 * * *). Mode dispatch logic is inside the dream prompt.

```
name: "auto-memory-dream"
schedule: { kind: "cron", expr: "30 4,10,16,22 * * *", tz: "<from autodream.json timezone>" }
payload: {
  kind: "agentTurn",
  message: "Run auto memory consolidation.\n\nRead skills/auto-dream/references/dream-prompt-lite.md and follow every step strictly.\n\nConfig: ~/.openclaw/autodream/autodream.json\nWorking directory: the workspace root",
  timeoutSeconds: 600
}
sessionTarget: "isolated"
delivery: { mode: "announce" }
```

### 3. Verify

- [ ] Cron job created and enabled
- [ ] `~/.openclaw/autodream/autodream.json` exists with valid modes
- [ ] `LTMEMORY.md` exists with section headers (use # LTMEMORY.md - Long-Horizon Meaning and History)
- [ ] `memory/index.json` exists
- [ ] `memory/procedures.md` exists
- [ ] `memory/.dream-log.md` exists

### 4. Cleanup

And finally cleanup the files on skills/auto-dream/:
- [ ] .git
- [ ] LICENSE
- [ ] README.md
- [ ] SETUP.md
