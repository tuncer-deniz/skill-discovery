# skill-discovery

OpenClaw skill lifecycle toolkit — discover new skills from session patterns, then monitor them for degradation.

## The Problem

Two things go wrong with agent skills:

1. **You don't create them.** You do the same thing 5 times before realizing "I should automate this."
2. **They silently break.** A skill that worked last month fails when models change, APIs shift, or codebases evolve.

This repo solves both.

## What's Included

### 🔍 Skill Discovery (SKILL.md)

Analyzes your OpenClaw session history to find:
- **Repeated task patterns** → New skill candidates
- **Re-learned lessons** → Rules for AGENTS.md
- **Multi-step workflows** → Automation opportunities
- **Cross-agent struggles** → Infrastructure improvements

Works as a behavioral skill — no scripts, just session analysis patterns your agent follows.

### 📊 Skill Health Tracker (skill-health.py)

Lightweight invocation logger that tracks which skills are failing and whether they're getting worse:

```bash
# Log results
./skill-health.py log github success
./skill-health.py log github failure --error "gh auth expired"

# Full report
./skill-health.py report

# Degrading skills only (for cron use)
./skill-health.py check
```

Example output:
```
Skill                Invocations  Fail Rate        Trend  Last Error
--------------------------------------------------------------------------------
github                        12       25%  ! degrading  gh auth token expired
weather                        8        0%       stable
todoist                        5       20%  * improving  API timeout
```

## Install

```bash
cd ~/.openclaw/skills
git clone https://github.com/tuncer-deniz/skill-discovery
chmod +x skill-discovery/skill-health.py
```

## Skill Discovery Usage

### Manual
```
Analyze my sessions from the last 7 days and identify skill candidates.
```

### Weekly Cron (Recommended)
```json
{
  "name": "weekly-skill-discovery",
  "schedule": { "kind": "cron", "expr": "0 10 * * 0", "tz": "America/Edmonton" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run skill discovery analysis on sessions from the last 7 days. Report findings with recommendations."
  },
  "sessionTarget": "isolated"
}
```

## Skill Health Usage

### Log invocations from your scripts
```bash
if some_command; then
    skill-health.py log my-skill success
else
    skill-health.py log my-skill failure --error "$(cat /tmp/last-error.txt)"
fi
```

### Weekly degradation check
```json
{
  "name": "weekly-skill-health-check",
  "schedule": { "kind": "cron", "expr": "0 9 * * 1" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run skill-health.py check. Report any degrading skills."
  },
  "sessionTarget": "isolated"
}
```

### Configuration

| Setting | Default | Override |
|---------|---------|----------|
| Data file | `~/.skill-health/data.json` | `SKILL_HEALTH_DATA` env var |
| Max entries | 500 (oldest rotated) | Edit `MAX_ENTRIES` in script |

## The Lifecycle

```
Discovery → Creation → Monitoring → Improvement
    ↑                                     |
    └─────────────────────────────────────┘
```

1. **Discovery** finds patterns worth automating
2. **skill-creator** scaffolds the new skill
3. **Health tracker** monitors it in production
4. When health degrades → discovery flags it for review

## Scoring Guide (Discovery)

| Score | Action |
|-------|--------|
| 5+ occurrences, >5 min each | Create skill immediately |
| 3-4 occurrences | Add to AGENTS.md |
| 2 occurrences | Note for observation |

## Real Discoveries

Patterns that became skills from actual usage:

| Pattern | Frequency | Result |
|---------|-----------|--------|
| Debugging cluster startup | 8x/week | `exo-cluster-ops` skill |
| Looking up config structure | 5x/week | AGENTS.md rule |
| Parsing session logs manually | 4x/week | This skill |

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw)
- Python 3.8+ (skill-health.py, no external deps)

## Inspired By

The observe → amend → evaluate loop from [cognee-skills](https://github.com/topoteretes/cognee) — stripped down to what most agent setups actually need.

## License

MIT

---

*A skill that helps you build more skills, then makes sure they keep working.*
