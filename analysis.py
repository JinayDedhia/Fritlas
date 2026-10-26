"""Transparent heuristics for the first Fritlas insights."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta


def summarize(events) -> dict:
    ordered = sorted(events, key=lambda event: event["occurred_at"])
    transitions = Counter()
    rapid_switches = 0

    for previous, current in zip(ordered, ordered[1:]):
        if previous["app_name"] == current["app_name"]:
            continue
        transitions[(previous["app_name"], current["app_name"])] += 1
        before = datetime.fromisoformat(previous["occurred_at"])
        after = datetime.fromisoformat(current["occurred_at"])
        if after - before <= timedelta(minutes=5):
            rapid_switches += 1

    transition_rows = [
        {"from": source, "to": target, "count": count}
        for (source, target), count in transitions.most_common(5)
    ]
    estimated_minutes = rapid_switches * 2
    return {
        "events": len(ordered),
        "rapid_switches": rapid_switches,
        "estimated_recovery_minutes": estimated_minutes,
        "top_transitions": transition_rows,
        "message": _message(rapid_switches, transition_rows),
    }


def _message(rapid_switches: int, transitions: list[dict]) -> str:
    if not rapid_switches:
        return "Keep tracking for a while. Insights appear after you switch between apps."
    if transitions:
        top = transitions[0]
        return (
            f"Your most repeated context shift is {top['from']} -> {top['to']} "
            f"({top['count']} times). Try batching that destination app."
        )
    return "You have some rapid context switches. Try writing a one-line next action before changing tasks."

