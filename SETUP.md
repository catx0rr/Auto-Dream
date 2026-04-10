## Setup

### 0. First Dream (Run Immediately After Install)

After setup is complete, DO NOT wait for the cron schedule. Immediately run the First Dream:

1. Read `runtime/first-dream-prompt.md`
2. Execute every step in the current session (not isolated — user should see it happen)
3. First Dream bypasses quality gates — consolidates everything to bootstrap the memory

### 1. Select Agent Profile

**Check for pre-selected profile first:**

If the environment variable `AUTODREAM_PROFILE` is set, use that value without prompting:

```bash
# Non-interactive (fleet rollout / automation)
export AUTODREAM_PROFILE=personal-assistant
# or
export AUTODREAM_PROFILE=business-employee
```

If `AUTODREAM_PROFILE` is not set, **ask the operator which profile to use:**

| Profile | File | Best for |
|---------|------|----------|
| `personal-assistant` | `profiles/personal-assistant.md` | Personal assistants, family assistants, butler/concierge, home-automation agents |
| `business-employee` | `profiles/business-employee.md` | Supervisor/owner DM, small GC teams, bounded operational workflows |

Read the selected profile to understand the recommended thresholds and markers.

**Home-automation assistants use the `personal-assistant` profile by default.**

### 2. Initialize Files

Working Directory `~/.openclaw/workspace`

```bash
mkdir -p ~/.openclaw/autodream
mkdir -p memory/episodes
```

### 3. Create Configuration

Create `autodream.json` using the preset from the selected profile.

**For personal-assistant profile** (`AUTODREAM_PROFILE=personal-assistant`):

Use the preset from `profiles/personal-assistant.md`. Write to `~/.openclaw/autodream/autodream.json`:

```json
{
  "version": "4.1",
  "profile": "personal-assistant",
  "activeModes": ["core", "rem", "deep"],
  "notificationLevel": "summary",
  "instanceName": "default",
  "timezone": "<operator timezone>",
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

**For business-employee profile** (`AUTODREAM_PROFILE=business-employee`):

Use the preset from `profiles/business-employee.md`. Write to `~/.openclaw/autodream/autodream.json`:

```json
{
  "version": "4.1",
  "profile": "business-employee",
  "activeModes": ["core", "rem", "deep"],
  "notificationLevel": "summary",
  "instanceName": "default",
  "timezone": "<operator timezone>",
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

**If updating an existing install:** preserve existing `timezone`, `notificationLevel`, `instanceName`, and `lastRun` values. Do not silently overwrite custom thresholds unless the operator explicitly asks to reprofile/reset.

Ensure the following files exist (create from `references/memory-template.md` templates if missing):
- `memory/index.json`
- `memory/procedures.md`
- `memory/.dream-log.md`
- `memory/.archive.md`

### 4. Resolve Auto-Dream Skill Path

Before creating the cron, resolve the actual installed path of the auto-dream skill so the cron payload uses an absolute path — not a hardcoded relative one.

#### 4a. Try standard skill roots first

```bash
for root in \
  "$HOME/.openclaw/workspace/skills" \
  "$HOME/.openclaw/workspace/.agents/skills" \
  "$HOME/.agents/skills" \
  "$HOME/.openclaw/skills"
do
  if [ -f "$root/auto-dream/runtime/auto-dream-prompt.md" ]; then
    export SKILL_ROOT="$root/auto-dream"
    break
  fi
done
```

#### 4b. If not found, check configured `extraDirs`

```bash
if [ -z "${SKILL_ROOT:-}" ]; then
  for root in $(openclaw config get skills.load.extraDirs --json 2>/dev/null | python3 -c "import json,sys; [print(d) for d in json.load(sys.stdin)]" 2>/dev/null); do
    if [ -f "$root/auto-dream/runtime/auto-dream-prompt.md" ]; then
      export SKILL_ROOT="$root/auto-dream"
      break
    fi
  done
fi
```

#### 4c. Fail if still unresolved

```bash
if [ -z "${SKILL_ROOT:-}" ] || [ ! -f "$SKILL_ROOT/runtime/auto-dream-prompt.md" ]; then
  echo "Could not locate auto-dream skill directory."
  echo "Install the skill first or ensure skills.load.extraDirs includes its parent root."
  exit 1
fi

dream_prompt_path="$SKILL_ROOT/runtime/auto-dream-prompt.md"
echo "Using SKILL_ROOT=$SKILL_ROOT"
echo "Dream prompt: $dream_prompt_path"
```

Verify `$dream_prompt_path` exists before proceeding.

### 5. Create Cron Job

Single cron at scheduled intervals (30 4,10,16,22 * * *). Mode dispatch logic is inside the dream prompt.

Use the resolved `$SKILL_ROOT` to construct the absolute path in the cron message. Example for personal-assistant profile:

```json
{
  "name": "auto-memory-dream",
  "schedule": { "kind": "cron", "expr": "30 4,10,16,22 * * *", "tz": "<timezone from autodream.json>" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run auto memory consolidation.\n\nRead <AUTODREAM_SKILL_ROOT>/runtime/auto-dream-prompt.md and follow every step strictly.\n\nConfig: ~/.openclaw/autodream/autodream.json\nWorking directory: the workspace root",
    "timeoutSeconds": 600
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```

Replace `<AUTODREAM_SKILL_ROOT>` with the resolved absolute path (e.g. `~/.openclaw/workspace/skills/cognitive/auto-dream`). The path must be absolute in the cron message so it works regardless of where the skill is installed.

### 6. Verify

- [ ] Profile selected and `autodream.json` contains `"profile"` field
- [ ] Cron job created and enabled
- [ ] `~/.openclaw/autodream/autodream.json` exists with profile-specific mode settings
- [ ] `LTMEMORY.md` exists with section headers (use # LTMEMORY.md - Long-Horizon Meaning and History)
- [ ] `memory/index.json` exists
- [ ] `memory/procedures.md` exists
- [ ] `memory/.dream-log.md` exists

### 7. Cleanup

Cleanup files in the installed Auto-Dream skill directory:
- [ ] .git
- [ ] LICENSE
- [ ] README.md
- [ ] SETUP.md
- [ ] profiles/