---
name: skill-discovery
description: Analyze session patterns to identify candidates for new skills, plugins, agents, or workflow rules. Self-improvement automation.
metadata: { "openclaw": { "emoji": "🔍" } }
---

# skill-discovery

Automatically discover opportunities to codify repeated workflows into skills, plugins, or rules.

## Overview

This skill analyzes your OpenClaw session history to find:
- **Repeated task patterns** → Skill candidates
- **Re-learned lessons** → AGENTS.md rules
- **Multi-step workflows** → Automation opportunities
- **Cross-agent struggles** → Shared infrastructure needs

## When to Use

- Weekly self-improvement review (recommended: schedule as cron)
- After a busy week with lots of ad-hoc tasks
- When you notice friction in your workflows
- Before planning automation improvements

## Manual Run

```
Analyze my sessions from the last 7 days and identify:
1. Repeated task patterns that could become skills
2. Rules I keep re-learning that should be in AGENTS.md
3. Multi-step workflows that could be automated
4. Things that caused the most friction
```

## Automated Weekly Check (Cron Setup)

```json
{
  "name": "weekly-skill-discovery",
  "schedule": { "kind": "cron", "expr": "0 10 * * 0", "tz": "America/Edmonton" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run skill discovery analysis on sessions from the last 7 days. Report findings with recommendations.",
    "timeoutSeconds": 600
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```

## Analysis Steps

### 1. Extract Session Data
```bash
# Find recent sessions
find ~/.openclaw/agents/*/sessions/ -name "*.jsonl" -mtime -7

# Extract user messages
jq -r 'select(.type=="message" and .message.role=="user") | 
  .message.content[]? | select(.type=="text") | .text' session.jsonl
```

### 2. Filter Out Noise
Remove automated/system messages:
- Cron triggers (`[cron:...`)
- Heartbeat prompts
- Pre-compaction flushes
- Timestamp prefixes

### 3. Cluster Patterns
Group similar requests by:
- **Action verbs** (create, fix, analyze, search, deploy)
- **Target objects** (config, skill, cron, agent, build)
- **Context** (project, tool, service)

### 4. Score Candidates
Prioritize by: `frequency × estimated_time_saved`

| Score | Action |
|-------|--------|
| 5+ occurrences, >5 min each | Create skill immediately |
| 3-4 occurrences | Add to AGENTS.md as rule |
| 2 occurrences | Note for observation |

### 5. Cross-Agent Analysis (Multi-Node)
If running multiple agents, SSH to other nodes:
```bash
ssh luna@<IP> 'find ~/.openclaw/agents/*/sessions/ -name "*.jsonl" -mtime -7'
ssh atlas@<IP> 'find ~/.openclaw/agents/*/sessions/ -name "*.jsonl" -mtime -7'
```

Issues appearing across multiple agents = highest priority.

## Output Format

```markdown
## Skill Discovery Report — Week of YYYY-MM-DD

### 🎯 Skill Candidates (create these)
1. **[name]** — [pattern description] — [frequency]x this week

### 📝 Rule Candidates (add to AGENTS.md)
1. **[rule]** — [why needed] — [frequency]x re-learned

### ⚙️ Automation Opportunities
1. **[workflow]** — [steps that could be scripted]

### 🔥 Friction Points
1. **[issue]** — [how often] — [suggested fix]

### 📊 Stats
- Sessions analyzed: N
- Unique patterns: N
- Agents covered: [list]
```

## Example Discoveries

**From real usage:**

| Pattern | Frequency | Became |
|---------|-----------|--------|
| Debugging exo cluster startup | 8x/week | `exo-cluster-ops` skill |
| Looking up OpenClaw config structure | 5x/week | AGENTS.md rule |
| Parsing session JSONL manually | 4x/week | This skill |
| SSH'ing to check agent status | 6x/week | Health check cron |

## Integration with Skill Creator

After identifying a candidate, use the `skill-creator` skill to scaffold it:
```
Create a new skill called [name] that [does X]. 
It should cover [patterns identified].
```

## Key Principles

1. **Frequency matters** — Don't skill-ify one-offs
2. **Time saved matters** — 10-second tasks aren't worth automating
3. **Cross-agent patterns** — If multiple agents struggle, fix at infrastructure level
4. **Rules before skills** — Sometimes a documented rule is better than code
5. **Iterate** — Run weekly, not just once

## Resources

- [OpenClaw session-logs skill](/opt/homebrew/lib/node_modules/openclaw/skills/session-logs/SKILL.md)
- [OpenClaw skill-creator skill](/opt/homebrew/lib/node_modules/openclaw/skills/skill-creator/SKILL.md)

---

*Meta-skill: helps you build more skills.*
