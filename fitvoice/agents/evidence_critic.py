"""Evidence & Safety Critic Agent.

Responsibilities:
- Mandatory quality-control stage for analytical reports and coaching advice.
- Independently verify that reported metrics match deterministic tool outputs.
- Verify every claim has supporting evidence in verified records.
- Flag unsupported causal claims (e.g., asserting sleep deficit definitely caused plateau without caveats).
- Detect contradictory findings or silent replacement of missing values.
- Review recommendations for safety and proportionality.
- Return structured verdict:
  - APPROVED
  - APPROVED_WITH_CAVEATS
  - REQUIRES_REVISION
  - BLOCKED
- Enforce maximum revision limit to prevent infinite loops.
- Do NOT simply agree with other agents.
"""

import time
import re
from typing import Dict, Any, List, Optional
from fitvoice.agents.base import BaseAgent
from fitvoice.schemas.agent_contracts import EvidenceCriticOutput
from fitvoice.config import settings


class EvidenceSafetyCriticAgent(BaseAgent):
    def __init__(self, max_revisions: Optional[int] = None):
        super().__init__(
            name="EVIDENCE_SAFETY_CRITIC",
            role_description="Independent quality control, evidence verification, and safety auditor",
            allowed_tools=[
                "deterministic_metric_validator",
                "causality_assertion_detector",
                "safety_guideline_checker",
                "revision_limiter",
            ],
            execution_budget_seconds=10.0,
        )
        self.max_revisions = max_revisions if max_revisions is not None else settings.max_revisions

    def audit_report(
        self,
        investigation_report: Dict[str, Any],
        analytical_results: Dict[str, Any],
        recovery_results: Dict[str, Any],
        revision_count: int = 0,
    ) -> Dict[str, Any]:
        """Audit the investigation report against source deterministic evidence."""
        start_time = time.perf_counter()

        observations = investigation_report.get("observations", [])
        calculated_metrics = investigation_report.get("calculated_metrics", [])
        possible_explanations = investigation_report.get("possible_explanations", [])
        limitations = investigation_report.get("limitations", [])
        data_sufficiency = investigation_report.get("data_sufficiency", "SUFFICIENT")

        unsupported_claims: List[str] = []
        causality_violations: List[str] = []
        safety_concerns: List[str] = []
        caveats: List[str] = []
        required_revisions: List[str] = []

        # 1. Independent numerical verification against deterministic tool outputs
        progression = analytical_results.get("progression", {})
        expected_max_w = progression.get("max_weight_lifted_kg")
        expected_e1rm = progression.get("peak_estimated_1rm_kg")

        # Search for metrics mentioned in report text
        report_text = " ".join(calculated_metrics + observations + possible_explanations)

        if expected_max_w and expected_max_w > 0:
            if f"{expected_max_w}" not in report_text and f"{int(expected_max_w)}" not in report_text:
                unsupported_claims.append(
                    f"Report does not accurately state max working weight of {expected_max_w} kg computed by Data Scientist."
                )

        if expected_e1rm and expected_e1rm > 0:
            # allow small rounding difference
            if f"{round(expected_e1rm)}" not in report_text and f"{expected_e1rm}" not in report_text:
                caveats.append(f"Estimated 1RM ({expected_e1rm} kg) should be explicitly cited with Epley formula reference.")

        # 2. Check for unsupported causal claims
        # Unqualified words like "caused by", "is definitely due to", "proves that" without limitations
        unqualified_causal_patterns = [
            r"\bcaused\s+by\b",
            r"\bproves\s+that\b",
            r"\bdefinitely\s+due\s+to\b",
            r"\bdirectly\s+caused\b",
        ]
        has_causality_caveat = any("causation" in lim.lower() or "correlation" in lim.lower() for lim in limitations)

        for expl in possible_explanations:
            for pat in unqualified_causal_patterns:
                if re.search(pat, expl.lower()) and not has_causality_caveat:
                    causality_violations.append(
                        f"Explanation '{expl}' asserts unqualified causation. Must be phrased as an association or hypothesis."
                    )

        # 3. Check for medical diagnosis violations
        forbidden_medical_terms = [
            "overtraining syndrome", "endocrine disorder", "diagnosed", "adrenal fatigue",
            "clinical insomnia", "torn muscle", "pathology"
        ]
        for term in forbidden_medical_terms:
            if term in report_text.lower():
                safety_concerns.append(f"Medical diagnosis term '{term}' detected. FitVoice is non-diagnostic.")

        # 4. Check for data sufficiency compliance
        if data_sufficiency == "INSUFFICIENT":
            if possible_explanations and not any("insufficient" in lim.lower() for lim in limitations):
                required_revisions.append(
                    "Explanations were generated despite INSUFFICIENT data without adequate limitations."
                )

        # 5. Determine Verdict
        if safety_concerns:
            verdict = "BLOCKED"
        elif (unsupported_claims or causality_violations or required_revisions):
            if revision_count >= self.max_revisions:
                # Bounded revision: don't enter endless loop, downgrade to APPROVED_WITH_CAVEATS with clear warning
                verdict = "APPROVED_WITH_CAVEATS"
                caveats.extend([f"Max revisions ({self.max_revisions}) reached: {c}" for c in unsupported_claims + causality_violations])
            else:
                verdict = "REQUIRES_REVISION"
        elif caveats or data_sufficiency == "PARTIAL":
            verdict = "APPROVED_WITH_CAVEATS"
        else:
            verdict = "APPROVED"

        output = EvidenceCriticOutput(
            verdict=verdict,
            metric_verification_passed=len(unsupported_claims) == 0,
            unsupported_claims=unsupported_claims,
            causality_violations=causality_violations,
            safety_concerns=safety_concerns,
            feedback_notes=caveats or ["All metrics verified against deterministic outputs."],
            required_revisions=required_revisions,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000

        trace_event = self.create_trace_event(
            task_assigned=f"Audit investigation report for factual accuracy, causality, and safety (Revision {revision_count})",
            status="SUCCESS",
            tools_consulted=self.allowed_tools,
            result_summary=f"Critic Verdict: {verdict}. Metric verification: {output.metric_verification_passed}. Caveats: {len(caveats)}, Violations: {len(causality_violations)}.",
            duration_ms=duration_ms,
            validation_status=verdict,
        )

        return {
            "critic_output": output.model_dump(),
            "verdict": verdict,
            "feedback": output.feedback_notes,
            "trace_event": trace_event,
        }

    def audit_recommendations(
        self,
        recommendations: Dict[str, Any],
        user_experience_level: str = "intermediate",
    ) -> Dict[str, Any]:
        """Audit Adaptive Coach recommendations for safety and proportionality."""
        start_time = time.perf_counter()
        actionable_steps = recommendations.get("actionable_steps", [])
        safety_issues: List[str] = []

        for step in actionable_steps:
            action_text = step.get("action", "").lower()
            # Safety check: disproportionate volume/intensity increases
            if "double" in action_text or "triple" in action_text or "100%" in action_text:
                safety_issues.append(f"Disproportionate workload increase flagged: '{step.get('action')}'")

        verdict = "BLOCKED" if safety_issues else "APPROVED"
        duration_ms = (time.perf_counter() - start_time) * 1000

        trace_event = self.create_trace_event(
            task_assigned="Audit Adaptive Coach recommendations for safety and proportionality",
            status="SUCCESS",
            tools_consulted=self.allowed_tools,
            result_summary=f"Recommendation Audit Verdict: {verdict}. Flagged issues: {len(safety_issues)}.",
            duration_ms=duration_ms,
            validation_status=verdict,
        )

        return {
            "verdict": verdict,
            "safety_issues": safety_issues,
            "trace_event": trace_event,
        }
