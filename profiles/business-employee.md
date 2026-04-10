# Auto-Dream Profile: Business Employee

**Agent type:** Bounded worker, supervisor/owner DM, small GC team workflows
**Memory emphasis:** Decisions, procedures, project state, team context, accountability

---

## When to use this profile

Use this profile for:

- Supervisor / owner DM agents
- Small group-chat team agents
- Bounded operational workflow agents
- Lower tolerance for casual preference promotion

These agents operate in a more structured topology: work conversations, team GCs, project channels. Promotion should be stricter for casual preferences and more focused on decisions, procedures, and accountability.

---

## Interaction topology

- Bounded — supervisor DM + small work GCs
- Decisions and procedures matter more than personal preferences
- Cross-session reinforcement is expected for important items
- Casual preferences should not promote as easily as in personal agents

---

## Default preset

```json
{
  "profile": "business-employee",
  "modes": {
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
  }
}
```

---

## Why these thresholds

- **Higher fastPathMinScore** — business agents should not fast-path casual observations. Only clearly high-signal entries should bypass regular gates.
- **Narrower fast-path markers** — no PREFERENCE or ROUTINE by default. Business agents care about HIGH, PIN, and PROCEDURE. Preferences and routines are less central to work memory.
- **Higher rem minRecallCount** — requires 3 recalls for rem promotion. Work items that matter get referenced across multiple interactions.
- **uniqueMode: day_or_session** — same as personal, but the narrower marker set and higher thresholds compensate for the topology difference.

---

## Fast-path markers

| Marker | Meaning |
|--------|---------|
| `HIGH` | High-importance entry (doubles base weight in scoring) |
| `PIN` | User-pinned — should promote quickly |
| `PROCEDURE` | Learned workflow or operational pattern |

Business agents do not include PREFERENCE or ROUTINE as fast-path markers by default. These can be added manually to `autodream.json` if the operator wants them.
