# Auto-Dream — Installation Guide

One-time installation of the Auto-Dream skill.
This is an **operator task** — run these commands on the host machine before agent setup.

**After installation, the agent runs [SETUP.md](SETUP.md) for first-time configuration.**

---

## Prerequisites

- Python 3.9+
- Git
- OpenClaw installed with a workspace at `~/.openclaw/workspace/`

---

## Step 0: Choose the Skill Install Root

### Option A — default workspace skills

```bash
export SKILL_PARENT="$HOME/.openclaw/workspace/skills"
```

### Option B — shared skill pack loaded through `extraDirs`

```bash
export SKILL_PARENT="$HOME/.openclaw/skills-pack/cognitive"
```

Derive the final skill path:

```bash
export SKILL_ROOT="$SKILL_PARENT/auto-dream"
mkdir -p "$SKILL_PARENT"
```

---

## Step 1: Install the Skill

```bash
git clone https://github.com/catx0rr/Auto-Dream.git "$SKILL_ROOT"
```

Verify:

```bash
ls "$SKILL_ROOT/SKILL.md"
```

---

## Step 2: If Needed, Register `extraDirs`

Skip this step if you installed into the default workspace skill root.

```bash
openclaw config set skills.load.extraDirs "[
  \"$SKILL_PARENT\"
]" --strict-json
```

---

## Post-Install Checklist

- [ ] `SKILL_PARENT` was chosen correctly
- [ ] `SKILL_ROOT` exists with `SKILL.md`
- [ ] `skills.load.extraDirs` was updated if using a non-default skill root

---

## Next Step

Tell the agent:

> Set up Auto-Dream. Read the installed `SETUP.md` in the `auto-dream` skill directory and follow every step.

---

## Important Notes

- The install location of the skill is **operator-chosen**
- The setup process **discovers the skill location dynamically**
- No external dependencies beyond Python 3.9+ and OpenClaw
- Runtime config is stored at `~/.openclaw/autodream/autodream.json`
