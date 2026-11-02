"""Tests for deterministic numerical tools and analytical functions."""

import pytest
from fitvoice.tools.workout_analytics import (
    calculate_epley_1rm,
    calculate_session_volume,
    analyze_exercise_progression,
    compare_two_periods,
    compute_personal_records,
)
from fitvoice.tools.recovery_analytics import (
    assess_recovery_data_sufficiency,
    compute_recovery_aggregates,
    compare_recovery_periods,
)


def test_epley_1rm_calculation():
    # 100kg x 1 rep = 100kg
    assert calculate_epley_1rm(100.0, 1) == 100.0
    # 100kg x 10 reps = 100 * (1 + 10/30) = 133.33 kg
    assert calculate_epley_1rm(100.0, 10) == 133.33
    # 0 weight or 0 reps returns 0.0
    assert calculate_epley_1rm(0.0, 5) == 0.0
    assert calculate_epley_1rm(100.0, 0) == 0.0


def test_session_volume_calculation():
    sets = [
        {"weight_kg": 100.0, "reps": 5},
        {"weight_kg": 100.0, "reps": 5},
        {"weight_kg": 80.0, "reps": 10},
    ]
    # (100*5) + (100*5) + (80*10) = 500 + 500 + 800 = 1800 kg
    assert calculate_session_volume(sets) == 1800.0


def test_analyze_exercise_progression():
    sets = [
        {"session_id": "s1", "date": "2026-10-01", "weight_kg": 80.0, "reps": 10, "set_id": "set1"},
        {"session_id": "s1", "date": "2026-10-01", "weight_kg": 85.0, "reps": 8, "set_id": "set2"},
        {"session_id": "s2", "date": "2026-10-04", "weight_kg": 90.0, "reps": 5, "set_id": "set3"},
    ]
    res = analyze_exercise_progression(sets, "Bench Press", "2026-10-01", "2026-10-07")
    assert res["total_sessions"] == 2
    assert res["total_sets"] == 3
    assert res["max_weight_lifted_kg"] == 90.0
    assert len(res["source_record_ids"]) == 3
    assert res["peak_estimated_1rm_kg"] > 100.0


def test_compare_two_periods_plateau():
    p1 = {
        "period_start": "2026-10-01",
        "period_end": "2026-10-14",
        "total_sessions": 4,
        "average_volume_per_session_kg": 2000.0,
        "peak_estimated_1rm_kg": 100.0,
    }
    p2 = {
        "period_start": "2026-10-15",
        "period_end": "2026-10-28",
        "total_sessions": 4,
        "average_volume_per_session_kg": 2010.0,
        "peak_estimated_1rm_kg": 100.5,
    }
    comp = compare_two_periods(p1, p2)
    assert comp["is_plateau_detected"] is True
    assert comp["e1rm_percent_change"] == 0.5


def test_compute_personal_records():
    sets = [
        {"exercise": "Bench Press", "weight_kg": 100.0, "reps": 3, "set_id": "s1", "date": "2026-10-01"},
        {"exercise": "Bench Press", "weight_kg": 105.0, "reps": 1, "set_id": "s2", "date": "2026-10-05"},
        {"exercise": "Squat", "weight_kg": 140.0, "reps": 5, "set_id": "s3", "date": "2026-10-03"},
    ]
    prs = compute_personal_records(sets)
    assert len(prs) == 2
    bench_pr = next(p for p in prs if p["exercise"] == "Bench Press")
    assert bench_pr["max_weight_kg"] == 105.0


def test_recovery_sufficiency_assessment():
    logs_sparse = [{"sleep_hours": 7.0}]
    suff_sparse = assess_recovery_data_sufficiency(logs_sparse, expected_days=28)
    assert suff_sparse["sufficiency_status"] == "INSUFFICIENT"

    logs_full = [{"sleep_hours": 7.5} for _ in range(25)]
    suff_full = assess_recovery_data_sufficiency(logs_full, expected_days=28)
    assert suff_full["sufficiency_status"] == "SUFFICIENT"


def test_recovery_aggregates_and_limitations():
    logs = [
        {"sleep_hours": 8.0, "soreness_score": 3, "energy_score": 7, "readiness_score": 8},
        {"sleep_hours": 6.0, "soreness_score": 7, "energy_score": 4, "readiness_score": 4},
    ]
    res = compute_recovery_aggregates(logs, "2026-10-01", "2026-10-02")
    assert res["average_sleep_hours"] == 7.0
    assert res["average_soreness"] == 5.0
    assert len(res["limitations"]) >= 2
    # Ensure guardrail against sleep architecture claim
    assert any("sleep architecture" in lim.lower() for lim in res["limitations"])
