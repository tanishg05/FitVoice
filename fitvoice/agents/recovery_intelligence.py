"""Recovery Intelligence Agent.

Responsibilities:
- Analyse recorded sleep duration, energy, soreness, and subjective readiness.
- Compare recovery metrics with workout dates and intensities.
- Identify associations only when sufficient observations exist.
- Detect missing data and inconsistent logging (sufficiency assessment).
- Strict guardrails:
  - Do NOT infer sleep quality from sleep duration alone.
  - Do NOT diagnose medical conditions (overtraining, injury, endocrine illness).
  - Do NOT present unvalidated composite scores as physiological facts.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fitvoice.agents.base import BaseAgent
from fitvoice.db.repository import FitnessRepository
from fitvoice.tools.recovery_analytics import (
    assess_recovery_data_sufficiency,
    compute_recovery_aggregates,
    compare_recovery_periods,
)
from fitvoice.schemas.agent_contracts import (
    RecoveryIntelligenceInput,
    RecoveryIntelligenceOutput,
)


class RecoveryIntelligenceAgent(BaseAgent):
    def __init__(self, repository: Optional[FitnessRepository] = None):
        super().__init__(
            name="RECOVERY_INTELLIGENCE",
            role_description="Evaluate recovery parameters, sleep trends, soreness, and logging sufficiency",
            allowed_tools=[
                "recovery_log_retrieval",
                "recovery_sufficiency_assessor",
                "recovery_aggregate_calculator",
                "recovery_period_comparator",
            ],
            execution_budget_seconds=10.0,
        )
        self.repository = repository or FitnessRepository()

    def process(
        self,
        user_id: str,
        days_back: int = 28,
        split_comparison: bool = True,
    ) -> Dict[str, Any]:
        """Process recovery metrics deterministically with strict guardrails."""
        start_time = time.perf_counter()
        today = datetime.now(timezone.utc).date()
        start_date = (today - timedelta(days=days_back)).isoformat()
        end_date = today.isoformat()

        # 1. Retrieve recovery logs
        logs = self.repository.get_recovery_logs(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 2. Sufficiency assessment
        sufficiency = assess_recovery_data_sufficiency(logs, expected_days=days_back)

        # 3. Overall aggregates
        overall_summary = compute_recovery_aggregates(logs, start_date, end_date)

        # 4. Period comparison (first half vs second half)
        period_comparison = {}
        if split_comparison and days_back >= 14:
            mid_date = (today - timedelta(days=days_back // 2)).isoformat()
            p1_logs = [l for l in logs if l.get("date", "") < mid_date]
            p2_logs = [l for l in logs if l.get("date", "") >= mid_date]

            p1_summary = compute_recovery_aggregates(p1_logs, start_date, mid_date)
            p2_summary = compute_recovery_aggregates(p2_logs, mid_date, end_date)
            period_comparison = compare_recovery_periods(p1_summary, p2_summary)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Structured summary text
        result_desc = (
            f"Sufficiency: {sufficiency['sufficiency_status']} ({sufficiency['logged_days']}/{days_back} days). "
            f"Avg sleep: {overall_summary.get('average_sleep_hours')}h, "
            f"Avg soreness: {overall_summary.get('average_soreness')}/10. "
        )
        if period_comparison.get("observed_associations"):
            result_desc += f"Associations found: {len(period_comparison['observed_associations'])}."

        trace_event = self.create_trace_event(
            task_assigned=f"Recovery evaluation and sufficiency audit for user '{user_id}' over {days_back} days",
            status="SUCCESS",
            tools_consulted=self.allowed_tools,
            result_summary=result_desc,
            duration_ms=duration_ms,
            validation_status="APPROVED",
        )

        return {
            "sufficiency": sufficiency,
            "overall_summary": overall_summary,
            "comparison": period_comparison,
            "observed_associations": period_comparison.get("observed_associations", []),
            "limitations": overall_summary.get("limitations", []),
            "total_logs": len(logs),
            "trace_event": trace_event,
        }

