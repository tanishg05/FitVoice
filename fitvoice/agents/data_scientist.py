"""Fitness Data Scientist Agent.

Responsibilities:
- Retrieve historical workout records using parameterised SQL.
- Calculate exercise volume, progression, estimated 1RM, consistency, and PRs.
- Identify missing observations and data-quality problems.
- NEVER invent numerical results: strictly use deterministic Python tools and SQL queries.
- Output explicit period, metric, units, and source record references.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fitvoice.agents.base import BaseAgent
from fitvoice.db.repository import FitnessRepository
from fitvoice.tools.workout_analytics import (
    analyze_exercise_progression,
    compare_two_periods,
    compute_personal_records,
)
from fitvoice.schemas.agent_contracts import (
    DataScientistInput,
    DataScientistOutput,
    MetricCalculation,
)


class FitnessDataScientistAgent(BaseAgent):
    def __init__(self, repository: Optional[FitnessRepository] = None):
        super().__init__(
            name="FITNESS_DATA_SCIENTIST",
            role_description="Deterministic numerical workout analysis, progression modeling, and PR calculation",
            allowed_tools=[
                "sql_parameterized_retrieval",
                "epley_1rm_calculator",
                "session_volume_aggregator",
                "period_progression_comparator",
                "personal_records_calculator",
            ],
            execution_budget_seconds=10.0,
        )
        self.repository = repository or FitnessRepository()

    def process(
        self,
        user_id: str,
        exercise_name: Optional[str] = None,
        days_back: int = 28,
        split_comparison: bool = True,
    ) -> Dict[str, Any]:
        """Execute deterministic fitness calculations over historical records."""
        start_time = time.perf_counter()
        today = datetime.now(timezone.utc).date()
        start_date = (today - timedelta(days=days_back)).isoformat()
        end_date = today.isoformat()

        # 1. Retrieve verified sets
        sets = self.repository.get_workout_sets(
            user_id=user_id,
            exercise=exercise_name,
            start_date=start_date,
            end_date=end_date,
            status="CONFIRMED",
        )

        # 2. Compute exercise progression
        progression = analyze_exercise_progression(
            sets=sets,
            exercise_name=exercise_name or "All Exercises",
            period_start=start_date,
            period_end=end_date,
        )

        # 3. Calculate Personal Records from raw sets
        all_time_sets = self.repository.get_workout_sets(
            user_id=user_id,
            exercise=exercise_name,
            status="CONFIRMED"
        )
        prs = compute_personal_records(all_time_sets)

        # 4. Two-period comparison (e.g. earlier 2 weeks vs recent 2 weeks)
        comparison_results = {}
        if split_comparison and days_back >= 14:
            mid_date = (today - timedelta(days=days_back // 2)).isoformat()
            p1_sets = [s for s in sets if s.get("date", "") < mid_date]
            p2_sets = [s for s in sets if s.get("date", "") >= mid_date]

            p1_summary = analyze_exercise_progression(
                p1_sets, exercise_name or "Exercise", start_date, mid_date
            )
            p2_summary = analyze_exercise_progression(
                p2_sets, exercise_name or "Exercise", mid_date, end_date
            )
            comparison_results = compare_two_periods(p1_summary, p2_summary)

        # 5. Build structured metrics list with units and source references
        metrics: List[MetricCalculation] = []
        if progression.get("total_volume_kg", 0) > 0:
            metrics.append(
                MetricCalculation(
                    period=f"{start_date} to {end_date}",
                    metric="total_volume_load",
                    value=progression["total_volume_kg"],
                    unit="kg",
                    source_record_ids=progression["source_record_ids"],
                    notes=f"Sum of volume across {progression['total_sessions']} sessions.",
                )
            )
        if progression.get("peak_estimated_1rm_kg", 0) > 0:
            metrics.append(
                MetricCalculation(
                    period=f"{start_date} to {end_date}",
                    metric="peak_estimated_1rm",
                    value=progression["peak_estimated_1rm_kg"],
                    unit="kg",
                    source_record_ids=progression["source_record_ids"][:5],
                    notes="Calculated via validated Epley formula.",
                )
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        summary = (
            f"Analyzed {len(sets)} sets across {progression.get('total_sessions', 0)} sessions. "
            f"Max weight: {progression.get('max_weight_lifted_kg', 0)} kg, "
            f"Peak E1RM: {progression.get('peak_estimated_1rm_kg', 0)} kg. "
        )
        if comparison_results.get("is_plateau_detected"):
            summary += "Stagnation detected between Period 1 and Period 2 (delta < 1.5%)."

        trace_event = self.create_trace_event(
            task_assigned=f"Deterministic numerical calculation for {exercise_name or 'user'} over {days_back} days",
            status="SUCCESS",
            tools_consulted=self.allowed_tools,
            result_summary=summary,
            duration_ms=duration_ms,
            validation_status="APPROVED",
        )

        return {
            "progression": progression,
            "comparison": comparison_results,
            "personal_records": prs,
            "metrics": [m.model_dump() for m in metrics],
            "data_quality_flags": progression.get("data_quality_flags", []),
            "total_records_analyzed": len(sets),
            "trace_event": trace_event,
        }
