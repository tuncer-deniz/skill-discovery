<p align="center">
  <img src="banner.png" alt="Skill Discovery" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Built%20for-OpenClaw-blueviolet?style=flat-square" alt="Built for OpenClaw">
  <a href="https://github.com/tuncer-deniz/skill-discovery/stargazers"><img src="https://img.shields.io/github/stars/tuncer-deniz/skill-discovery?style=flat-square" alt="GitHub Stars"></a>
  <a href="https://x.com/tuncerdeniz"><img src="https://img.shields.io/badge/follow-%40tuncerdeniz-1DA1F2?style=flat-square&logo=x&logoColor=white" alt="Follow @tuncerdeniz"></a>
</p>

# skill-discovery v2.0.0

OpenClaw skill lifecycle toolkit — discover new skills from session patterns, then monitor them for degradation.

## The Problem

Two things go wrong with agent skills:

1. **You don't create them.** You do the same thing 5 times before realizing "I should automate this."
2. **They silently break.** A skill that worked last month fails when models change, APIs shift, or codebases evolve.

This repo solves both.

## What's New in v2

### 🧠 LCM as a Data Source
Before reading raw JSONL, the skill now queries LCM summaries first. LCM captures compacted history that raw session files lose after compaction — patterns from weeks ago are often only visible there. Uses `lcm_grep` and `lcm_expand_query`.

### 🔴 Operational Anomaly Detection
Three new checks run alongside pattern discovery:
- **Camofox tab leaks** — sessions that opened browser tabs without closing them
- **Workspace file bloat** — context files >15KB eating your token budget (MEMORY.md, AGENTS.md, etc.)
- **Cron failure patterns** — consecutive failures on the same job = broken automation that needs immediate attention

### 🤖 Subagent Delegation Gap Detection
Identifies sessions where the main agent did too much work inline: >15 tool calls + >3 different tool types + zero `sessions_spawn` = delegation miss. Flags them as refactor candidates to keep main session context lean.

### 🔗 Tool Sequence Pattern Matching
Looks for repeated tool-call sequences across sessions (same 3+ tool types in same order, appearing 3+ times). Example: `web_fetch → exec → message send` repeated 4x = a research-and-report workflow worth scripting into a dedicated skill.

---

## What's Included

### 🔍 Skill Discovery (SKILL.md)

Analyzes your OpenClaw session history to find:
- **Repeated task patterns** → New skill candidates
- **Re-learned lessons** → Rules for AGENTS.md
- **Multi-step workflows** → Automation opportunities
- **Cross-agent struggles** → Infrastructure improvements
- **Operational anomalies** → Leaks, bloat, broken crons
- **Delegation gaps** → Tasks that should have used subagents

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

> **Custom workspace path:** If your OpenClaw data lives somewhere other than `~/.openclaw`, set `CLAWD_WORKSPACE`:
> ```bash
> export CLAWD_WORKSPACE=/path/to/your/workspace
> ```
> The skill's session-find commands respect this variable.

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
| Workspace | `~/.openclaw` | `CLAWD_WORKSPACE` env var |
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
| `web_fetch → exec → message` loop | 4x/week | `research-report` skill |

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw)
- Python 3.8+ (skill-health.py, no external deps)

## Inspired By

The observe → amend → evaluate loop from [cognee-skills](https://github.com/topoteretes/cognee) — stripped down to what most agent setups actually need.

## License

MIT

---

*A skill that helps you build more skills, then makes sure they keep working.*
