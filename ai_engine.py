"""Small, local, explainable behavior model. No cloud or API key required."""

from __future__ import annotations

from datetime import datetime, timezone
from math import sqrt

import storage


def _vector(row):
    active = max(float(row["active_seconds"]), 1.0)
    return [float(row["mouse_distance"]) / active, float(row["switches"]), float(row["idle_seconds"]) / active]


def _distance(left, right):
    return sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _centroid(vectors):
    return [sum(values) / len(vectors) for values in zip(*vectors)]


def feedback_for_latest() -> dict:
    """Clusters recent behavior into two modes and explains the current mode."""
    rows = [dict(row) for row in reversed(storage.recent_behavior_samples())]
    if not rows:
        return {"label": "Learning", "message": "Fritlas needs a few minutes of activity before it can learn your patterns."}
    current = rows[-1]
    current_vector = _vector(current)
    if len(rows) < 6:
        return {"label": "Learning", "message": f"Learning your baseline from {len(rows)} activity windows. Add a check-in to personalize feedback."}
    vectors = [_vector(row) for row in rows]
    centers = [vectors[0], vectors[-1]]
    groups = [[], []]
    for _ in range(6):
        groups = [[], []]
        for vector in vectors:
            groups[0 if _distance(vector, centers[0]) <= _distance(vector, centers[1]) else 1].append(vector)
        centers = [_centroid(group) if group else centers[index] for index, group in enumerate(groups)]
    current_group = 0 if _distance(current_vector, centers[0]) <= _distance(current_vector, centers[1]) else 1
    typical_switches = sum(vector[1] for vector in vectors) / len(vectors)
    check_in = storage.latest_check_in()
    context = f" Your stated intention: {check_in['intention']}." if check_in else ""
    if current_vector[1] > max(1.0, typical_switches * 1.5):
        return {"label": "Fragmented mode", "message": f"This activity window has above-baseline context switching. Pick one next action before opening another app.{context}"}
    if current_vector[2] > 0.3:
        return {"label": "Recovery mode", "message": f"You have been away from the keyboard for part of this window. Resume with a small, explicit task.{context}"}
    if current["category"] == "focus" and current_group in (0, 1):
        return {"label": "Focus mode", "message": f"Your current pattern resembles a focused work block: low switching and sustained activity.{context}"}
    return {"label": "Steady mode", "message": f"Your activity is near your learned baseline. Add a check-in if you want feedback tied to a goal.{context}"}


def generate_and_store_feedback() -> dict:
    result = feedback_for_latest()
    storage.add_feedback(datetime.now(timezone.utc).isoformat(), result["label"], result["message"])
    return result
