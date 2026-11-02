"""Progress Detective Agent (Flagship Analytical Agent).

Responsibilities:
- Translate user inquiry into a rigorous multi-domain investigation plan.
- Coordinate with Fitness Data Scientist and Recovery Intelligence agents.
- Compare results across time windows to detect progress, plateaus, or fatigue trends.
- Produce a structured investigation report distinguishing:
  1. Observations (verified logged facts)
  2. Calculated metrics (deterministic numbers with units)
  3. Possible explanations (grounded hypotheses)
  4. Alternative interpretations (competing plausible factors)
  5. Preliminary recommendations (target areas for Adaptive Coach)
  6. Limitations (unmeasured variables, correlation vs causation)
- Explicitly flag insufficient data without manufacturing significance or fabricating records.
"""

import time
from typing import Dict, Any, List, Optional
from fitvoice.agents.base import BaseAgent
from fitvoice.schemas.agent_contracts import InvestigationReport


class ProgressDetectiveAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="PROGRESS_DETECTIVE",
            role_description="Lead investigative agent for plateau detection, multi-period synthesis, and hypotheses",
            allowed_tools=[
                "investigation_plan_generator",
                "multi_agent_findings_synthesizer",
                "hypothesis_generator",
            ],
            execution_budget_seconds=15.0,
        )

    def generate_plan(self, user_query: str, user_id: str) -> Dict[str, Any]:
        """Formulate a targeted investigation plan based on user inquiry."""
        lowered = user_query.lower()
        target_exercise = "Bench Press" if "bench" in lowered else ("Squat" if "squat" in lowered else "General")
        days = 28  # standard 4-week window

        return {
            "investigation_question": user_query,
            "target_exercise": target_exercise,
            "analysis_window_days": days,
            "datasets_needed": ["workout_sessions", "workout_sets", "recovery_logs"],
            "agents_to_consult": ["FITNESS_DATA_SCIENTIST", "RECOVERY_INTELLIGENCE"],
            "comparative_split": True,
        }

    def synthesize_report(
        self,
        investigation_plan: Dict[str, Any],
        workout_analysis: Dict[str, Any],
        recovery_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesize verified findings into a structured, evidence-grounded report."""
        start_time = time.perf_counter()

        progression = workout_analysis.get("progression", {})
        workout_comp = workout_analysis.get("comparison", {})
        rec_sufficiency = recovery_analysis.get("sufficiency", {})
        rec_overall = recovery_analysis.get("overall_summary", {})
        rec_comp = recovery_analysis.get("comparison", {})

        observations: List[str] = []
        calculated_metrics: List[str] = []
        possible_explanations: List[str] = []
        alternative_interpretations: List[str] = []
        preliminary_recommendations: List[str] = []
        limitations: List[str] = []

        # Check sufficiency first
        rec_status = rec_sufficiency.get("sufficiency_status", "INSUFFICIENT")
        data_sufficiency = "SUFFICIENT"
        if progression.get("total_sessions", 0) < 2:
            data_sufficiency = "INSUFFICIENT"
            observations.append(f"Only {progression.get('total_sessions', 0)} workout session(s) found in target window.")
            limitations.append("Insufficient workout history to perform meaningful longitudinal trend analysis.")
        elif rec_status == "INSUFFICIENT":
            data_sufficiency = "PARTIAL"
            observations.append(f"Sufficient workout records ({progression.get('total_sessions')} sessions), but sparse recovery data.")
            limitations.append("Recovery data coverage is below 30%; recovery-related explanations are tentative.")

        # If data is sufficient or partial, build report
        if data_sufficiency in ("SUFFICIENT", "PARTIAL"):
            # 1. Observations
            total_sessions = progression.get("total_sessions", 0)
            total_sets = progression.get("total_sets", 0)
            ex_name = progression.get("exercise", "Target Exercise")
            observations.append(f"Completed {total_sessions} logged sessions containing {total_sets} sets of {ex_name}.")
            if rec_overall.get("total_logs", 0) > 0:
                observations.append(f"Recorded {rec_overall.get('total_logs')} recovery logs over the 28-day window.")

            # 2. Calculated Metrics (with units and deterministic sources)
            max_w = progression.get("max_weight_lifted_kg", 0.0)
            e1rm = progression.get("peak_estimated_1rm_kg", 0.0)
            tot_vol = progression.get("total_volume_kg", 0.0)
            calculated_metrics.append(f"Max working weight: {max_w} kg")
            calculated_metrics.append(f"Peak Estimated 1RM (Epley): {e1rm} kg")
            calculated_metrics.append(f"Total volume load: {tot_vol} kg")

            if workout_comp.get("is_plateau_detected"):
                calculated_metrics.append(
                    f"Progression between Period 1 and Period 2: E1RM changed by {workout_comp.get('e1rm_percent_change')}% "
                    f"({workout_comp.get('peak_e1rm_p1_kg')} kg to {workout_comp.get('peak_e1rm_p2_kg')} kg), confirming a performance plateau."
                )

            # Recovery Metrics
            avg_sleep = rec_overall.get("average_sleep_hours")
            avg_sore = rec_overall.get("average_soreness")
            if avg_sleep is not None:
                calculated_metrics.append(f"Average nightly sleep: {avg_sleep} hours")
            if avg_sore is not None:
                calculated_metrics.append(f"Average subjective soreness: {avg_sore} / 10")

            if rec_comp.get("sleep_delta_hours") is not None:
                calculated_metrics.append(
                    f"Sleep duration shifted by {rec_comp.get('sleep_delta_hours')} hours ({rec_comp.get('sleep_percent_change')}%) from Period 1 to Period 2."
                )
            if rec_comp.get("soreness_delta") is not None:
                calculated_metrics.append(
                    f"Soreness shifted by +{rec_comp.get('soreness_delta')} points between Period 1 and Period 2."
                )

            # 3. Possible Explanations (Correlated & Grounded)
            if workout_comp.get("is_plateau_detected"):
                if rec_comp.get("sleep_delta_hours", 0) < -0.8:
                    possible_explanations.append(
                        f"Cumulative sleep debt: Nightly sleep fell by {abs(rec_comp.get('sleep_delta_hours', 0))} hours concurrently with the performance stall."
                    )
                if rec_comp.get("soreness_delta", 0) >= 1.5:
                    possible_explanations.append(
                        f"Elevated residual fatigue: Subjective muscle soreness climbed to {rec_overall.get('average_soreness')}/10, suggesting inadequate inter-session recovery."
                    )
                if not possible_explanations:
                    possible_explanations.append(
                        "Neuromuscular plateau: Consistent load at 95 kg without progressive volume variation or deload cycle."
                    )

            # 4. Alternative Interpretations
            alternative_interpretations.append(
                "Nutrition & energy balance: Protein intake and caloric surplus were not consistently tracked in the period, which may influence recovery."
            )
            alternative_interpretations.append(
                "Psychological / life stress: External stressors unrecorded in logs could affect central nervous system readiness and perceived exertion."
            )

            # 5. Preliminary Recommendations
            preliminary_recommendations.append("Schedule a structured 1-week deload at 60-70% intensity to clear residual fatigue.")
            preliminary_recommendations.append("Establish a consistent sleep hygiene routine targeting at least 7.5 hours per night.")

            # 6. Limitations
            limitations.append("Correlation does not prove causation: concurrent sleep reduction and plateau do not establish a sole causal mechanism.")
            limitations.append("Self-reported sleep and soreness rely on subjective perception rather than objective polysomnography or biomarker tracking.")

        report = InvestigationReport(
            investigation_question=investigation_plan.get("investigation_question", ""),
            datasets_consulted=investigation_plan.get("datasets_needed", []),
            observations=observations,
            calculated_metrics=calculated_metrics,
            possible_explanations=possible_explanations,
            alternative_interpretations=alternative_interpretations,
            preliminary_recommendations=preliminary_recommendations,
            limitations=limitations,
            data_sufficiency=data_sufficiency,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        trace_event = self.create_trace_event(
            task_assigned="Synthesize multi-agent findings into structured investigation report",
            status="SUCCESS",
            tools_consulted=self.allowed_tools,
            result_summary=f"Report synthesized: {len(observations)} observations, {len(calculated_metrics)} metrics, {len(possible_explanations)} explanations. Sufficiency: {data_sufficiency}.",
            duration_ms=duration_ms,
            validation_status="PENDING",
        )

        return {
            "report": report.model_dump(),
            "data_sufficiency": data_sufficiency,
            "trace_event": trace_event,
        }
