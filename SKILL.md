---
name: skill-discovery
description: Skill lifecycle toolkit — discover new skills from session patterns, then monitor them for degradation with skill-health.py.
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
- **Operational anomalies** → Leaks, bloat, and broken automation
- **Delegation gaps** → Tasks that should have used subagents

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
5. Operational anomalies (tab leaks, file bloat, cron failures)
6. Subagent delegation gaps
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

### 0. Query LCM First (New in v2)

Before reading raw JSONL, check LCM summaries — they capture compacted history that the raw files no longer contain:

```
lcm_grep pattern="repeated|again|always|every time"
```

Use `lcm_expand_query` to drill into specific patterns found:
```
lcm_expand_query query="repeated workflow friction" prompt="What tasks does the agent do repeatedly that could be automated?"
```

LCM is especially valuable because raw JSONL entries are pruned after compaction — patterns that happened weeks ago are often only visible in LCM summaries.

### 1. Extract Session Data
```bash
# Find recent sessions
find ~/.openclaw/agents/*/sessions/ -name "*.jsonl" -mtime -7

# Extract user messages
jq -r 'select(.type=="message" and .message.role=="user") | 
  .message.content[]? | select(.type=="text") | .text' session.jsonl
```

> **Custom workspace:** If your sessions live elsewhere, set `CLAWD_WORKSPACE` env var:
> ```bash
> export CLAWD_WORKSPACE=/path/to/your/workspace
> find $CLAWD_WORKSPACE/agents/*/sessions/ -name "*.jsonl" -mtime -7
> ```

### 2. Filter Out Noise
Remove automated/system messages:
- Cron triggers (`[cron:...`)
- Heartbeat prompts (`Read HEARTBEAT.md`)
- Pre-compaction flushes
- Timestamp prefixes

**Heartbeat sessions:** Bucket separately — don't discard entirely. Heartbeat-initiated sessions are valid automation signal (they reveal what the agent monitors and how), but they dominate the user message corpus (~70% of sessions in a typical week). Mixing them into organic request clustering drowns out real user patterns. Analyze them in a dedicated "Automation Health" section instead.

### 3. Cluster Patterns
Group similar requests by:
- **Action verbs** (create, fix, analyze, search, deploy)
- **Target objects** (config, skill, cron, agent, build)
- **Context** (project, tool, service)

#### Tool Sequence Pattern Matching (New in v2)

Look for repeated tool-call sequences — the same 3+ tool types in the same order appearing 3+ times across sessions:

```bash
# Extract tool call sequences per session
jq -r 'select(.type=="tool_use") | .name' session.jsonl | paste - - - | sort | uniq -c | sort -rn
```

Example: `web_fetch → exec → message send` appearing 4 times = a research-and-report workflow worth scripting into a dedicated skill.

Flag any sequence appearing 3+ times as an automation candidate.

### 4. Score Candidates
Prioritize by: `frequency × estimated_time_saved`

| Score | Action |
|-------|--------|
| 5+ occurrences, >5 min each | Create skill immediately |
| 3-4 occurrences | Add to AGENTS.md as rule |
| 2 occurrences | Note for observation |

### 5. Operational Anomaly Detection (New in v2)

Check for operational problems that silently degrade agent performance:

#### Camofox Tab Leaks
```bash
# Sessions that opened tabs without closing them
jq -r 'select(.type=="tool_use") | .name' session.jsonl | grep -E "camofox_(create_tab|close_tab)"
```
If `camofox_create_tab` count exceeds `camofox_close_tab` count in a session → tab leak. Browsers accumulate, memory climbs, bot-detection fingerprints diverge.

**Remediation:** When a session is flagged as a chronic tab-leaker (2+ consecutive runs with unclosed tabs):
1. Identify the cron job name from the session metadata
2. Link to its instruction/skill file for editing
3. Add `camofox_close_tab` to the teardown path in the skill/cron instructions
4. Run `camofox-cleanup.sh` (from openclaw-optimization) to close leaked tabs immediately
5. If the cron runs nightly, verify the fix on the next run — don't wait for next week's report

#### Workspace File Bloat
```bash
wc -c ~/.openclaw/MEMORY.md ~/.openclaw/AGENTS.md ~/.openclaw/BRAIN.md 2>/dev/null
```
Files >15KB are eating context budget every session. Flag for pruning:
- `MEMORY.md` >15KB → archive old entries
- `AGENTS.md` >15KB → split into domain files
- `BRAIN.md` >10KB → trim completed tasks

#### Cron Failure Patterns
```bash
# Check for consecutive failures on same job
grep "FAILED\|error\|exit code [^0]" ~/.openclaw/cron-logs/*.log | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn
```
2+ consecutive failures on the same job = broken automation. Surface immediately, don't wait for weekly review.

### 6. Subagent Delegation Gap Detection (New in v2)

Identify sessions where the main agent did too much work inline:

```bash
# Sessions with high tool diversity but no subagent spawn
jq -s '
  group_by(.session_id)[] |
  {
    session: .[0].session_id,
    tool_calls: [.[] | select(.type=="tool_use")] | length,
    tool_types: [.[] | select(.type=="tool_use") | .name] | unique | length,
    spawned: ([.[] | select(.type=="tool_use" and .name=="sessions_spawn")] | length)
  } |
  select(.tool_calls > 15 and .tool_types > 3 and .spawned == 0)
' *.jsonl
```

Sessions with >15 tool calls, >3 different tool types, and zero `sessions_spawn` = delegation miss. Flag these as candidates for subagent refactoring — the main session context likely bloated unnecessarily.

**Cron/organic split:** Before flagging, check if the session was cron-initiated (look for `[cron:` prefix or `cron` in session metadata). Cron-automated tasks (bookmark researcher, signal runner, intel dashboard) legitimately run 20-50+ tools inline by design — they're isolated sessions whose context dies after the run. Only flag organic (user-initiated) sessions as delegation gaps.

### 7. Cross-Agent Analysis (Multi-Node)
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

### 🔴 Operational Anomalies
1. **[issue type]** — [details] — [severity]

### 🤖 Delegation Gaps
1. **[session]** — [N tool calls, M tool types, 0 spawns] — [refactor candidate]

### 🔥 Friction Points
1. **[issue]** — [how often] — [suggested fix]

### 📊 Stats
- Sessions analyzed: N
- LCM summaries queried: N
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
| `web_fetch → exec → message` sequence | 4x/week | `research-report` skill |

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
5. **LCM before JSONL** — Compacted history is only in LCM; check it first
6. **Anomalies are urgent** — Tab leaks and broken crons don't wait for weekly review
7. **Iterate** — Run weekly, not just once

## Resources

- [OpenClaw session-logs skill](/opt/homebrew/lib/node_modules/openclaw/skills/session-logs/SKILL.md)
- [OpenClaw skill-creator skill](/opt/homebrew/lib/node_modules/openclaw/skills/skill-creator/SKILL.md)

---

## Skill Health Monitoring

This skill also includes `skill-health.py` — a lightweight tracker for skill invocation success/failure rates.

### Commands
```bash
skill-health.py log <skill> success|failure [--error "msg"]   # Log result
skill-health.py report                                         # Full report
skill-health.py check                                          # Degrading only (cron)
```

### Cron Integration
```json
{
  "name": "weekly-skill-health-check",
  "schedule": { "kind": "cron", "expr": "0 9 * * 1" },
  "payload": { "kind": "agentTurn", "message": "Run skill-health.py check. Report any degrading skills." },
  "sessionTarget": "isolated"
}
```

Data stored at `~/.skill-health/data.json` (override with `SKILL_HEALTH_DATA` env var). Python 3 stdlib only.

---

*Skill lifecycle: discover → create → monitor → improve.*
