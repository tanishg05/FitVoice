"""Deterministic recovery analytics and safe association analysis.

Strict Guardrails Enforced:
1. Sleep duration is never equated with sleep quality or architecture.
2. No medical diagnoses (e.g. overtraining syndrome, endocrine dysfunction, injury).
3. No fabricated physiological composite scores presented as clinical fact.
4. Associations are explicitly marked as correlational observations, not causation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def assess_recovery_data_sufficiency(
    recovery_logs: List[Dict[str, Any]],
    expected_days: int,
) -> Dict[str, Any]:
    """Check whether sufficient recovery observations exist to justify an analysis."""
    logged_count = len(recovery_logs)
    if expected_days <= 0:
        expected_days = max(logged_count, 1)

    compliance_ratio = round(logged_count / expected_days, 2)

    if logged_count == 0 or compliance_ratio < 0.30:
        sufficiency = "INSUFFICIENT"
        notes = f"Only {logged_count} recovery logs found across {expected_days} days (<30% coverage)."
    elif compliance_ratio < 0.70:
        sufficiency = "PARTIAL"
        notes = f"{logged_count} recovery logs across {expected_days} days ({int(compliance_ratio * 100)}% coverage)."
    else:
        sufficiency = "SUFFICIENT"
        notes = f"{logged_count} recovery logs across {expected_days} days ({int(compliance_ratio * 100)}% coverage)."

    return {
        "sufficiency_status": sufficiency,
        "logged_days": logged_count,
        "expected_days": expected_days,
        "compliance_ratio": compliance_ratio,
        "notes": notes,
    }


def compute_recovery_aggregates(
    recovery_logs: List[Dict[str, Any]],
    period_start: str,
    period_end: str,
) -> Dict[str, Any]:
    """Calculate deterministic summary statistics over recovery logs."""
    if not recovery_logs:
        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_logs": 0,
            "average_sleep_hours": None,
            "min_sleep_hours": None,
            "max_sleep_hours": None,
            "average_soreness": None,
            "average_energy": None,
            "average_readiness": None,
            "limitations": ["No recovery records logged in this period."],
        }

    sleep_values = [float(r["sleep_hours"]) for r in recovery_logs if r.get("sleep_hours") is not None]
    soreness_values = [int(r["soreness_score"]) for r in recovery_logs if r.get("soreness_score") is not None]
    energy_values = [int(r["energy_score"]) for r in recovery_logs if r.get("energy_score") is not None]
    readiness_values = [int(r["readiness_score"]) for r in recovery_logs if r.get("readiness_score") is not None]

    avg_sleep = round(sum(sleep_values) / len(sleep_values), 2) if sleep_values else None
    avg_soreness = round(sum(soreness_values) / len(soreness_values), 2) if soreness_values else None
    avg_energy = round(sum(energy_values) / len(energy_values), 2) if energy_values else None
    avg_readiness = round(sum(readiness_values) / len(readiness_values), 2) if readiness_values else None

    limitations = [
        "Sleep hours reflect total self-reported time and do not assess sleep architecture (REM/Deep) or fragmentation.",
        "Soreness and readiness ratings are subjective self-assessments and do not constitute clinical or physiological diagnostics.",
    ]

    return {
        "period_start": period_start,
        "period_end": period_end,
        "total_logs": len(recovery_logs),
        "average_sleep_hours": avg_sleep,
        "min_sleep_hours": min(sleep_values) if sleep_values else None,
        "max_sleep_hours": max(sleep_values) if sleep_values else None,
        "average_soreness": avg_soreness,
        "average_energy": avg_energy,
        "average_readiness": avg_readiness,
        "limitations": limitations,
    }


def compare_recovery_periods(
    p1_summary: Dict[str, Any],
    p2_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare recovery metrics between two discrete observation periods."""
    s1 = p1_summary.get("average_sleep_hours")
    s2 = p2_summary.get("average_sleep_hours")
    sleep_delta = round(s2 - s1, 2) if (s1 is not None and s2 is not None) else None
    sleep_pct = round((sleep_delta / s1 * 100.0), 2) if (s1 and sleep_delta is not None) else None

    sor1 = p1_summary.get("average_soreness")
    sor2 = p2_summary.get("average_soreness")
    soreness_delta = round(sor2 - sor1, 2) if (sor1 is not None and sor2 is not None) else None

    read1 = p1_summary.get("average_readiness")
    read2 = p2_summary.get("average_readiness")
    readiness_delta = round(read2 - read1, 2) if (read1 is not None and read2 is not None) else None

    associations = []
    if sleep_delta is not None and sleep_delta <= -1.0:
        associations.append(
            f"Sleep duration decreased by {abs(sleep_delta)} hours/night ({abs(sleep_pct)}%) from period 1 to period 2."
        )
    if soreness_delta is not None and soreness_delta >= 1.5:
        associations.append(
            f"Subjective muscle soreness increased by {soreness_delta} points (on a 1-10 scale) between periods."
        )
    if readiness_delta is not None and readiness_delta <= -1.5:
        associations.append(
            f"Subjective readiness decreased by {abs(readiness_delta)} points between periods."
        )

    return {
        "sleep_delta_hours": sleep_delta,
        "sleep_percent_change": sleep_pct,
        "soreness_delta": soreness_delta,
        "readiness_delta": readiness_delta,
        "observed_associations": associations,
        "guardrail_notice": "Observed associations indicate temporal co-occurrence, not clinical causality.",
    }
