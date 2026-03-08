# skill-discovery

OpenClaw skill for discovering new skill/automation opportunities by analyzing your session patterns.

## The Meta-Problem

You do the same thing 5 times before realizing "I should automate this." This skill catches those patterns automatically.

## What It Does

Analyzes your OpenClaw session history to find:
- **Repeated task patterns** → New skill candidates
- **Re-learned lessons** → Rules for AGENTS.md
- **Multi-step workflows** → Automation opportunities
- **Cross-agent struggles** → Infrastructure improvements

## Install

```bash
cd ~/.openclaw/skills
git clone https://github.com/tuncer-deniz/skill-discovery
```

Or copy `SKILL.md` manually:
```bash
mkdir -p ~/.openclaw/skills/skill-discovery
cp SKILL.md ~/.openclaw/skills/skill-discovery/
```

## Usage

### Manual Analysis
```
Analyze my sessions from the last 7 days and identify skill candidates.
```

### Weekly Cron (Recommended)
```json
{
  "name": "weekly-skill-discovery",
  "schedule": { "kind": "cron", "expr": "0 10 * * 0" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run skill discovery analysis on sessions from the last 7 days."
  },
  "sessionTarget": "isolated"
}
```

## How It Works

1. **Extract** — Parse session JSONL files for user messages
2. **Filter** — Remove cron triggers, heartbeats, system noise
3. **Cluster** — Group similar requests by action/target/context
4. **Score** — Prioritize by `frequency × time_saved`
5. **Report** — Output candidates with recommendations

## Scoring Guide

| Score | Action |
|-------|--------|
| 5+ occurrences, >5 min each | Create skill immediately |
| 3-4 occurrences | Add to AGENTS.md |
| 2 occurrences | Note for observation |

## Example Discoveries

Real patterns that became skills:

| Pattern | Frequency | Result |
|---------|-----------|--------|
| Debugging cluster startup | 8x/week | `exo-cluster-ops` skill |
| Looking up config structure | 5x/week | AGENTS.md rule |
| Parsing session logs manually | 4x/week | This skill |

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw)
- Session history (the more, the better)

## License

MIT

---

*A skill that helps you build more skills. Very meta.*
