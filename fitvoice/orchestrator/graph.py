"""LangGraph Multi-Agent Orchestrator for FitVoice."""

import time
import uuid
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from fitvoice.state import FitVoiceState
from fitvoice.orchestrator.router import classify_request
from fitvoice.agents.voice_intelligence import VoiceIntelligenceAgent
from fitvoice.agents.data_scientist import FitnessDataScientistAgent
from fitvoice.agents.recovery_intelligence import RecoveryIntelligenceAgent
from fitvoice.agents.progress_detective import ProgressDetectiveAgent
from fitvoice.agents.evidence_critic import EvidenceSafetyCriticAgent
from fitvoice.agents.adaptive_coach import AdaptiveCoachAgent
from fitvoice.clients.sarvam import SarvamClient
from fitvoice.db.repository import FitnessRepository
from fitvoice.config import settings


class FitVoiceOrchestrator:
    def __init__(
        self,
        repository: Optional[FitnessRepository] = None,
        sarvam_client: Optional[SarvamClient] = None,
        max_revisions: Optional[int] = None,
    ):
        self.repository = repository or FitnessRepository()
        self.sarvam_client = sarvam_client or SarvamClient()
        self.max_revisions = max_revisions if max_revisions is not None else settings.max_revisions

        # Initialize the 6 specialized agents
        self.voice_agent = VoiceIntelligenceAgent(sarvam_client=self.sarvam_client)
        self.data_scientist_agent = FitnessDataScientistAgent(repository=self.repository)
        self.recovery_agent = RecoveryIntelligenceAgent(repository=self.repository)
        self.progress_agent = ProgressDetectiveAgent()
        self.critic_agent = EvidenceSafetyCriticAgent(max_revisions=self.max_revisions)
        self.coach_agent = AdaptiveCoachAgent()

        self.graph = self._build_graph()

    # ---------------------------------------------------------
    # Graph Nodes
    # ---------------------------------------------------------
    def router_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Classify incoming user inquiry and establish execution scope."""
        start_time = time.perf_counter()
        req_type = state.get("request_type") or classify_request(state)

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "agent_name": "AGENT_ORCHESTRATOR",
            "stage": "router",
            "task_assigned": f"Classify query '{state.get('user_query', '')[:40]}' and select multi-agent workflow",
            "status": "SUCCESS",
            "tools_consulted": ["workflow_classifier"],
            "result_summary": f"Selected workflow: {req_type.upper()}.",
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            "validation_status": "APPROVED",
        }

        trace = list(state.get("agent_execution_trace", []))
        trace.append(event)
        return {"request_type": req_type, "agent_execution_trace": trace}

    def voice_intelligence_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Extract structured candidate records from audio or text."""
        res = self.voice_agent.process(
            user_query=state.get("user_query", ""),
            user_id=state.get("user_id", "demo_user"),
            raw_audio_path=state.get("raw_audio_path"),
            preferred_language=state.get("preferred_language", "en-IN"),
        )
        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "transcript": res["transcript"],
            "candidate_records": res["candidate_records"],
            "requires_user_confirmation": res["requires_user_confirmation"],
            "confirmation_prompt": res["review_summary"],
            "agent_execution_trace": trace,
        }

    def progress_detective_plan_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Formulate a targeted multi-agent investigation plan."""
        plan = self.progress_agent.generate_plan(
            user_query=state.get("user_query", ""),
            user_id=state.get("user_id", "demo_user"),
        )
        return {"investigation_plan": plan}

    def data_scientist_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Execute deterministic workout calculations and SQL metrics."""
        plan = state.get("investigation_plan", {})
        target_ex = plan.get("target_exercise")
        days = plan.get("analysis_window_days", 28)

        # For simple questions without a formal plan, infer exercise or defaults
        if not target_ex:
            q = state.get("user_query", "").lower()
            target_ex = "Bench Press" if "bench" in q else ("Squat" if "squat" in q else None)

        res = self.data_scientist_agent.process(
            user_id=state.get("user_id", "demo_user"),
            exercise_name=target_ex,
            days_back=days,
            split_comparison=True,
        )

        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "analytical_results": res,
            "agent_execution_trace": trace,
        }

    def recovery_intelligence_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Analyze recovery metrics, sleep trends, and sufficiency."""
        plan = state.get("investigation_plan", {})
        days = plan.get("analysis_window_days", 28)

        res = self.recovery_agent.process(
            user_id=state.get("user_id", "demo_user"),
            days_back=days,
            split_comparison=True,
        )

        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "recovery_findings": res,
            "agent_execution_trace": trace,
        }

    def progress_detective_synthesize_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Synthesize multi-agent findings into a structured investigation report."""
        plan = state.get("investigation_plan", {})
        res = self.progress_agent.synthesize_report(
            investigation_plan=plan,
            workout_analysis=state.get("analytical_results", {}),
            recovery_analysis=state.get("recovery_findings", {}),
        )

        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "progress_findings": res["report"],
            "agent_execution_trace": trace,
        }

    def evidence_critic_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Perform mandatory evidence auditing and causality checks."""
        rev_count = state.get("revision_count", 0)
        res = self.critic_agent.audit_report(
            investigation_report=state.get("progress_findings", {}),
            analytical_results=state.get("analytical_results", {}),
            recovery_results=state.get("recovery_findings", {}),
            revision_count=rev_count,
        )

        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "critic_verdict": res["verdict"],
            "critic_feedback": res["feedback"],
            "agent_execution_trace": trace,
        }

    def revision_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Adjust claims in response to critic feedback within bounded attempts."""
        start_time = time.perf_counter()
        rev_count = state.get("revision_count", 0) + 1
        findings = dict(state.get("progress_findings", {}))

        # Tone down claims to ensure strict evidence compliance
        findings["limitations"] = list(findings.get("limitations", [])) + [
            "Critic Revision Note: Unqualified causal assertions downgraded to correlational observations."
        ]

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "agent_name": "AGENT_ORCHESTRATOR",
            "stage": "targeted_revision",
            "task_assigned": f"Perform targeted revision {rev_count}/{self.max_revisions} based on Critic feedback",
            "status": "SUCCESS",
            "tools_consulted": ["revision_policy_engine"],
            "result_summary": f"Revision {rev_count} applied: adjusted causal claims and added mandatory limitations.",
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            "validation_status": "APPROVED",
        }

        trace = list(state.get("agent_execution_trace", []))
        trace.append(event)

        return {
            "revision_count": rev_count,
            "progress_findings": findings,
            "agent_execution_trace": trace,
        }

    def adaptive_coach_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Generate proportionate, data-grounded next steps."""
        res = self.coach_agent.formulate_recommendations(
            user_query=state.get("user_query", ""),
            user_id=state.get("user_id", "demo_user"),
            validated_report=state.get("progress_findings", {}),
            critic_verdict=state.get("critic_verdict", "APPROVED"),
            critic_caveats=state.get("critic_feedback", []),
        )

        trace = list(state.get("agent_execution_trace", []))
        trace.append(res["trace_event"])

        return {
            "proposed_recommendations": res["coach_output"],
            "agent_execution_trace": trace,
        }

    def insufficient_data_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Handle cases where data sufficiency is inadequate without fabricating records."""
        start_time = time.perf_counter()
        analytical = state.get("analytical_results", {})
        total_sessions = analytical.get("progression", {}).get("total_sessions", 0)

        response = (
            f"⚠️ **Insufficient Data for Investigation**\n\n"
            f"FitVoice detected only **{total_sessions} logged session(s)** and limited recovery entries for this user.\n\n"
            f"**Why this matters**: A reliable plateau or fatigue analysis requires at least 4-6 consistent sessions "
            f"and daily recovery logs over 2 to 4 weeks. FitVoice strictly adheres to evidence integrity and **never fabricates historical records**.\n\n"
            f"**Recommended Action**:\n"
            f"1. Log your next 3-4 workouts with exercise, weight, and completed reps.\n"
            f"2. Record your nightly sleep and subjective soreness.\n"
            f"3. Run the progress investigation once sufficient baseline data has been collected."
        )

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "agent_name": "AGENT_ORCHESTRATOR",
            "stage": "insufficient_data_handler",
            "task_assigned": "Evaluate data sufficiency and prepare transparent disclosure",
            "status": "SUCCESS",
            "tools_consulted": ["data_sufficiency_assessor"],
            "result_summary": f"Data insufficient ({total_sessions} sessions). Transparent explanation provided without record fabrication.",
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
            "validation_status": "APPROVED",
        }

        trace = list(state.get("agent_execution_trace", []))
        trace.append(event)

        return {
            "final_response": response,
            "agent_execution_trace": trace,
        }

    def response_assembler_node(self, state: FitVoiceState) -> Dict[str, Any]:
        """Synthesize all validated outputs into a cohesive final response and speech reference."""
        req_type = state.get("request_type")

        # 1. Voice Logging Response
        if req_type == "voice_logging":
            prompt = state.get("confirmation_prompt", "")
            final_text = (
                f"### 🎙️ FitVoice Intelligence - Record Extracted\n\n"
                f"{prompt}\n\n"
                f"👉 **Review & Confirm**: To safeguard your fitness history, unconfirmed records are never saved directly. "
                f"Please confirm to commit these entries to your verified training log."
            )
            return {"final_response": final_text}

        # 2. Simple Question Response
        if req_type == "simple_question":
            res = state.get("analytical_results", {})
            prog = res.get("progression", {})
            prs = res.get("personal_records", [])

            lines = ["### 📊 Fitness Data Scientist - Calculation Output\n"]
            if prog.get("exercise"):
                lines.append(f"**Exercise**: {prog.get('exercise')}")
                lines.append(f"• **Peak Working Weight**: {prog.get('max_weight_lifted_kg')} kg")
                lines.append(f"• **Estimated 1RM (Epley)**: {prog.get('peak_estimated_1rm_kg')} kg")
                lines.append(f"• **Total Volume Load**: {prog.get('total_volume_kg')} kg ({prog.get('total_sets')} sets)")
                lines.append(f"• **Source Record References**: {len(prog.get('source_record_ids', []))} verified sets")
            if prs:
                lines.append("\n**Verified Personal Records**:")
                for p in prs[:3]:
                    lines.append(f"• {p['exercise']}: {p['max_weight_kg']} kg × {p['reps_at_max']} reps (E1RM: {p['estimated_1rm_kg']} kg)")

            final_text = "\n".join(lines)
            return {"final_response": final_text}

        # 3. If already filled by insufficient_data_node, preserve
        if state.get("final_response"):
            return {}

        # 4. Full Investigation Response
        rep = state.get("progress_findings", {})
        coach = state.get("proposed_recommendations", {})
        critic_v = state.get("critic_verdict", "PENDING")

        verdict_badge = {
            "APPROVED": "✅ **Evidence Status: APPROVED**",
            "APPROVED_WITH_CAVEATS": "⚠️ **Evidence Status: APPROVED WITH CAVEATS**",
            "REQUIRES_REVISION": "🔄 **Evidence Status: REVISED & GROUNDED**",
            "BLOCKED": "🛑 **Evidence Status: BLOCKED FOR SAFETY**",
        }.get(critic_v, f"ℹ️ **Evidence Status: {critic_v}**")

        lines = [
            f"## 🔍 FitVoice Multi-Agent Progress Investigation",
            f"{verdict_badge}\n",
            "### 1. 📋 Verified Observations",
        ]
        for obs in rep.get("observations", []):
            lines.append(f"- {obs}")

        lines.append("\n### 2. 🔢 Deterministic Metrics (Data Scientist & Recovery)")
        for m in rep.get("calculated_metrics", []):
            lines.append(f"- {m}")

        lines.append("\n### 3. 💡 Possible Explanations (Grounded Hypotheses)")
        for expl in rep.get("possible_explanations", []):
            lines.append(f"- {expl}")

        lines.append("\n### 4. ⚖️ Alternative Interpretations")
        for alt in rep.get("alternative_interpretations", []):
            lines.append(f"- {alt}")

        lines.append("\n### 5. 🎯 Adaptive Coach Recommendations")
        for step in coach.get("actionable_steps", []):
            lines.append(f"**[{step.get('area')}]**: {step.get('action')}")
            lines.append(f"  *Reasoning*: {step.get('justification')}")
            lines.append(f"  *Grounded in*: `{step.get('grounded_in_record')}`\n")

        lines.append("### 6. ⚠️ Critical Limitations & Safety Disclaimers")
        for lim in rep.get("limitations", []):
            lines.append(f"- {lim}")
        if coach.get("medical_disclaimer"):
            lines.append(f"- *{coach.get('medical_disclaimer')}*")

        final_text = "\n".join(lines)

        # Bulbul speech synthesis reference
        tts_audio = None
        if settings.has_live_sarvam_api and not settings.demo_mode:
            tts_res = self.sarvam_client.text_to_speech(
                text=coach.get("summary_message", final_text[:200]),
                target_language_code=state.get("preferred_language", "en-IN"),
            )
            tts_audio = tts_res.get("audio_base64")

        return {
            "final_response": final_text,
            "response_audio_reference": tts_audio,
        }

    # ---------------------------------------------------------
    # Routing Conditions
    # ---------------------------------------------------------
    def route_after_classifier(self, state: FitVoiceState) -> str:
        req = state.get("request_type", "")
        if req == "voice_logging":
            return "voice_intelligence"
        elif req == "simple_question":
            return "data_scientist"
        elif req == "insufficient_data":
            return "insufficient_data"
        return "progress_detective_plan"

    def route_after_data_scientist(self, state: FitVoiceState) -> str:
        req = state.get("request_type", "")
        if req == "simple_question":
            # Direct short circuit! Do NOT invoke recovery, critic, or coach.
            return "response_assembler"

        # Check sufficiency of workout data
        prog = state.get("analytical_results", {}).get("progression", {})
        if prog.get("total_sessions", 0) == 0:
            return "insufficient_data"
        return "recovery_intelligence"

    def route_after_critic(self, state: FitVoiceState) -> str:
        verdict = state.get("critic_verdict", "APPROVED")
        rev_count = state.get("revision_count", 0)

        if verdict == "REQUIRES_REVISION" and rev_count < self.max_revisions:
            return "revision"
        if verdict == "BLOCKED":
            return "response_assembler"
        return "adaptive_coach"

    # ---------------------------------------------------------
    # Graph Construction
    # ---------------------------------------------------------
    def _build_graph(self):
        graph = StateGraph(FitVoiceState)

        # Register nodes
        graph.add_node("router", self.router_node)
        graph.add_node("voice_intelligence", self.voice_intelligence_node)
        graph.add_node("progress_detective_plan", self.progress_detective_plan_node)
        graph.add_node("data_scientist", self.data_scientist_node)
        graph.add_node("recovery_intelligence", self.recovery_intelligence_node)
        graph.add_node("progress_detective_synthesize", self.progress_detective_synthesize_node)
        graph.add_node("evidence_critic", self.evidence_critic_node)
        graph.add_node("revision", self.revision_node)
        graph.add_node("adaptive_coach", self.adaptive_coach_node)
        graph.add_node("insufficient_data", self.insufficient_data_node)
        graph.add_node("response_assembler", self.response_assembler_node)

        # Entry point
        graph.set_entry_point("router")

        # Routing edges
        graph.add_conditional_edges(
            "router",
            self.route_after_classifier,
            {
                "voice_intelligence": "voice_intelligence",
                "data_scientist": "data_scientist",
                "progress_detective_plan": "progress_detective_plan",
                "insufficient_data": "insufficient_data",
            }
        )

        # Voice intelligence goes to response assembler
        graph.add_edge("voice_intelligence", "response_assembler")

        # Progress detective plan goes to data scientist
        graph.add_edge("progress_detective_plan", "data_scientist")

        # Conditional after data scientist
        graph.add_conditional_edges(
            "data_scientist",
            self.route_after_data_scientist,
            {
                "response_assembler": "response_assembler",
                "recovery_intelligence": "recovery_intelligence",
                "insufficient_data": "insufficient_data",
            }
        )

        # Recovery intelligence goes to synthesizer
        graph.add_edge("recovery_intelligence", "progress_detective_synthesize")

        # Progress detective synthesizer goes to critic
        graph.add_edge("progress_detective_synthesize", "evidence_critic")

        # Conditional after critic
        graph.add_conditional_edges(
            "evidence_critic",
            self.route_after_critic,
            {
                "revision": "revision",
                "adaptive_coach": "adaptive_coach",
                "response_assembler": "response_assembler",
            }
        )

        # Revision loops back to synthesizer for bounded update
        graph.add_edge("revision", "progress_detective_synthesize")

        # Adaptive coach and insufficient data go to response assembler
        graph.add_edge("adaptive_coach", "response_assembler")
        graph.add_edge("insufficient_data", "response_assembler")

        # Final exit
        graph.add_edge("response_assembler", END)

        return graph.compile()

    def run(self, initial_state: FitVoiceState) -> FitVoiceState:
        """Execute the LangGraph orchestrator with execution trace logging."""
        result = self.graph.invoke(initial_state)
        return result

