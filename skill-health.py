#!/usr/bin/env python3
"""
Skill Health Tracker for OpenClaw
Lightweight invocation logger + failure rate monitor for agent skills.

Track which skills are failing, how often, and whether they're getting worse.
Designed to run alongside OpenClaw crons/heartbeats.

Usage:
    skill-health.py log <skill> success|failure [--error "msg"]
    skill-health.py report
    skill-health.py check
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Default data location — override with SKILL_HEALTH_DATA env var
DATA_FILE = Path(os.environ.get("SKILL_HEALTH_DATA", Path.home() / ".skill-health" / "data.json"))
MAX_ENTRIES = 500


def load_data():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save_data(entries):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def cmd_log(skill, result, error=None):
    entries = load_data()
    entry = {
        "skill": skill,
        "result": result,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    save_data(entries)
    print(f"Logged {result} for '{skill}'")


def failure_rate(entries):
    if not entries:
        return 0.0
    failures = sum(1 for e in entries if e["result"] == "failure")
    return failures / len(entries)


def last_error(entries):
    for e in reversed(entries):
        if e["result"] == "failure" and e.get("error"):
            return e["error"]
    return None


def split_by_window(skill_entries):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    recent, prev = [], []
    for e in skill_entries:
        ts = datetime.fromisoformat(e["timestamp"])
        if ts >= week_ago:
            recent.append(e)
        elif ts >= two_weeks_ago:
            prev.append(e)
    return recent, prev


def trend_label(recent_rate, prev_rate):
    delta = recent_rate - prev_rate
    if abs(delta) < 0.05:
        return "stable"
    return "degrading" if delta > 0 else "improving"


def get_skills(entries):
    skills = {}
    for e in entries:
        skills.setdefault(e["skill"], []).append(e)
    return skills


def cmd_report():
    entries = load_data()
    if not entries:
        print("No data yet. Run 'skill-health.py log <skill> success' to start tracking.")
        return

    skills = get_skills(entries)
    print(f"{'Skill':<20} {'Invocations':>11} {'Fail Rate':>10} {'Trend':>12}  Last Error")
    print("-" * 80)
    for skill, skill_entries in sorted(skills.items()):
        recent, prev = split_by_window(skill_entries)
        rate = failure_rate(recent) if recent else failure_rate(skill_entries)
        prev_rate = failure_rate(prev)
        trend = trend_label(rate, prev_rate) if prev else "-"
        err = last_error(skill_entries) or ""
        if len(err) > 35:
            err = err[:32] + "..."
        trend_icons = {"degrading": "! ", "improving": "* ", "stable": "  "}
        icon = trend_icons.get(trend, "  ")
        print(f"{skill:<20} {len(skill_entries):>11} {rate:>9.0%} {icon + trend:>12}  {err}")


def cmd_check():
    entries = load_data()
    if not entries:
        return

    skills = get_skills(entries)
    found = False
    for skill, skill_entries in sorted(skills.items()):
        recent, prev = split_by_window(skill_entries)
        if not recent or not prev:
            continue
        recent_rate = failure_rate(recent)
        prev_rate = failure_rate(prev)
        if recent_rate > prev_rate + 0.05:
            err = last_error(skill_entries) or "no error message"
            print(
                f"WARNING {skill}: {recent_rate:.0%} failure rate "
                f"(was {prev_rate:.0%} last week) -- last error: {err}"
            )
            found = True

    if not found:
        print("All skills healthy.")


def main():
    parser = argparse.ArgumentParser(
        description="Skill Health Tracker for OpenClaw",
        epilog="Data stored at: %(default)s (override with SKILL_HEALTH_DATA env var)",
    )
    sub = parser.add_subparsers(dest="command")

    log_p = sub.add_parser("log", help="Log a skill invocation result")
    log_p.add_argument("skill", help="Skill name")
    log_p.add_argument("result", choices=["success", "failure"], help="Result")
    log_p.add_argument("--error", help="Error message (for failures)", default=None)

    sub.add_parser("report", help="Full summary of all tracked skills")
    sub.add_parser("check", help="Only degrading skills (for cron/heartbeat)")

    args = parser.parse_args()

    if args.command == "log":
        cmd_log(args.skill, args.result, args.error)
    elif args.command == "report":
        cmd_report()
    elif args.command == "check":
        cmd_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
