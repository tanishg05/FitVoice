"""Deterministic workout analytical calculations and parameterised metrics.

Mathematical Formulas:
- Epley 1RM formula: weight * (1 + reps / 30.0)
- Brzycki 1RM formula: weight * (36.0 / (37.0 - reps))
- Total Volume Load: sum(weight_kg * reps) for all sets
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def calculate_epley_1rm(weight_kg: float, reps: int) -> float:
    """Calculate Estimated 1-Rep Max using the validated Epley formula."""
    if reps <= 0 or weight_kg <= 0:
        return 0.0
    if reps == 1:
        return round(weight_kg, 2)
    return round(weight_kg * (1.0 + (reps / 30.0)), 2)


def calculate_session_volume(sets: List[Dict[str, Any]]) -> float:
    """Calculate total volume load in kg: sum(weight_kg * reps)."""
    return round(sum(float(s.get("weight_kg", 0.0)) * int(s.get("reps", 0)) for s in sets), 2)


def analyze_exercise_progression(
    sets: List[Dict[str, Any]],
    exercise_name: str,
    period_start: str,
    period_end: str,
) -> Dict[str, Any]:
    """Perform deterministic analysis of an exercise over a specified date window."""
    if not sets:
        return {
            "exercise": exercise_name,
            "period_start": period_start,
            "period_end": period_end,
            "total_sets": 0,
            "total_volume_kg": 0.0,
            "average_volume_per_session_kg": 0.0,
            "max_weight_lifted_kg": 0.0,
            "peak_estimated_1rm_kg": 0.0,
            "source_record_ids": [],
            "data_quality_flags": ["No sets found for the exercise in this window."],
        }

    # Group by session_id / date
    sessions_map: Dict[str, List[Dict[str, Any]]] = {}
    record_ids: List[str] = []
    data_quality_flags: List[str] = []

    for s in sets:
        sid = s.get("session_id") or s.get("date")
        sessions_map.setdefault(sid, []).append(s)
        if s.get("set_id"):
            record_ids.append(s["set_id"])

        # Data quality checks
        if s.get("weight_kg", 0) <= 0:
            data_quality_flags.append(f"Set {s.get('set_id', 'unknown')} has non-positive weight.")
        if s.get("reps", 0) <= 0:
            data_quality_flags.append(f"Set {s.get('set_id', 'unknown')} has non-positive reps.")

    total_volume = 0.0
    session_summaries = []
    max_weight = 0.0
    peak_e1rm = 0.0
    peak_e1rm_source = None

    for sid, s_sets in sessions_map.items():
        sess_date = s_sets[0].get("date", "unknown")
        sess_vol = calculate_session_volume(s_sets)
        total_volume += sess_vol

        sess_max_w = max(float(s.get("weight_kg", 0.0)) for s in s_sets)
        sess_peak_e1rm = max(calculate_epley_1rm(float(s.get("weight_kg", 0.0)), int(s.get("reps", 0))) for s in s_sets)

        if sess_max_w > max_weight:
            max_weight = sess_max_w

        if sess_peak_e1rm > peak_e1rm:
            peak_e1rm = sess_peak_e1rm
            peak_e1rm_source = sid

        session_summaries.append({
            "session_id": sid,
            "date": sess_date,
            "sets_count": len(s_sets),
            "volume_kg": sess_vol,
            "top_weight_kg": sess_max_w,
            "top_e1rm_kg": sess_peak_e1rm,
        })

    session_summaries.sort(key=lambda x: x["date"])
    avg_vol = round(total_volume / len(sessions_map), 2) if sessions_map else 0.0

    return {
        "exercise": exercise_name,
        "period_start": period_start,
        "period_end": period_end,
        "total_sessions": len(sessions_map),
        "total_sets": len(sets),
        "total_volume_kg": round(total_volume, 2),
        "average_volume_per_session_kg": avg_vol,
        "max_weight_lifted_kg": max_weight,
        "peak_estimated_1rm_kg": peak_e1rm,
        "peak_e1rm_source_session": peak_e1rm_source,
        "sessions": session_summaries,
        "source_record_ids": record_ids,
        "data_quality_flags": data_quality_flags,
    }


def compare_two_periods(
    p1_data: Dict[str, Any],
    p2_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare two discrete periods deterministically to compute deltas."""
    vol1 = p1_data.get("average_volume_per_session_kg", 0.0)
    vol2 = p2_data.get("average_volume_per_session_kg", 0.0)
    vol_delta = round(vol2 - vol1, 2)
    vol_pct_change = round((vol_delta / vol1 * 100.0), 2) if vol1 > 0 else 0.0

    e1rm1 = p1_data.get("peak_estimated_1rm_kg", 0.0)
    e1rm2 = p2_data.get("peak_estimated_1rm_kg", 0.0)
    e1rm_delta = round(e1rm2 - e1rm1, 2)
    e1rm_pct_change = round((e1rm_delta / e1rm1 * 100.0), 2) if e1rm1 > 0 else 0.0

    sessions1 = p1_data.get("total_sessions", 0)
    sessions2 = p2_data.get("total_sessions", 0)

    # Check for stagnation / plateau: delta within +/- 1.5%
    is_stagnant = abs(e1rm_pct_change) < 1.5 and sessions1 >= 3 and sessions2 >= 3

    return {
        "period_1_range": f"{p1_data.get('period_start')} to {p1_data.get('period_end')}",
        "period_2_range": f"{p2_data.get('period_start')} to {p2_data.get('period_end')}",
        "period_1_sessions": sessions1,
        "period_2_sessions": sessions2,
        "volume_per_session_p1_kg": vol1,
        "volume_per_session_p2_kg": vol2,
        "volume_change_kg": vol_delta,
        "volume_percent_change": vol_pct_change,
        "peak_e1rm_p1_kg": e1rm1,
        "peak_e1rm_p2_kg": e1rm2,
        "e1rm_change_kg": e1rm_delta,
        "e1rm_percent_change": e1rm_pct_change,
        "is_plateau_detected": is_stagnant,
    }


def compute_personal_records(sets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Determine all-time verified personal records from sets."""
    if not sets:
        return []

    # Group by exercise
    by_ex: Dict[str, List[Dict[str, Any]]] = {}
    for s in sets:
        ex = s.get("exercise", "Unknown").title()
        by_ex.setdefault(ex, []).append(s)

    prs = []
    for ex, ex_sets in by_ex.items():
        best_set = max(ex_sets, key=lambda s: float(s.get("weight_kg", 0.0)))
        best_e1rm_set = max(
            ex_sets,
            key=lambda s: calculate_epley_1rm(float(s.get("weight_kg", 0.0)), int(s.get("reps", 0)))
        )
        best_e1rm = calculate_epley_1rm(float(best_e1rm_set.get("weight_kg", 0.0)), int(best_e1rm_set.get("reps", 0)))

        prs.append({
            "exercise": ex,
            "max_weight_kg": float(best_set.get("weight_kg", 0.0)),
            "reps_at_max": int(best_set.get("reps", 0)),
            "date": best_set.get("date", "unknown"),
            "set_id": best_set.get("set_id", best_set.get("id")),
            "estimated_1rm_kg": best_e1rm,
            "e1rm_set_id": best_e1rm_set.get("set_id", best_e1rm_set.get("id")),
        })

    return prs
