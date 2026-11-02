"""High-level execution runner and resilient pipeline for FitVoice."""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from fitvoice.state import FitVoiceState, create_initial_state
from fitvoice.orchestrator.graph import FitVoiceOrchestrator
from fitvoice.clients.sarvam import SarvamClient, SarvamAPIError
from fitvoice.db.repository import FitnessRepository
from fitvoice.config import settings

logger = logging.getLogger("fitvoice.orchestrator.runner")


def run_pipeline(
    user_query: str,
    user_id: str = "alex_lifter",
    preferred_language: str = "en-IN",
    raw_audio_path: Optional[str] = None,
    orchestrator: Optional[FitVoiceOrchestrator] = None,
    repository: Optional[FitnessRepository] = None,
    sarvam_client: Optional[SarvamClient] = None,
) -> FitVoiceState:
    """Execute the multi-agent FitVoice pipeline with error trapping and trace preservation."""
    start_wall = time.perf_counter()
    state = create_initial_state(
        user_query=user_query,
        user_id=user_id,
        preferred_language=preferred_language,
        raw_audio_path=raw_audio_path,
    )

    orch = orchestrator or FitVoiceOrchestrator(
        repository=repository,
        sarvam_client=sarvam_client,
    )

    try:
        final_state = orch.run(state)
        return final_state
    except SarvamAPIError as api_err:
        # Workflow E: API failure handling
        logger.error(f"Workflow E caught Sarvam API failure: {api_err}")
        err_msg = (
            f"⚠️ **Sarvam AI Service Notice**: The speech or language model service encountered a temporary error "
            f"(HTTP {api_err.status_code or 'Unknown'}). Your query `{user_query}` has been preserved.\n\n"
            f"FitVoice strictly refuses to fabricate live AI inference. You may retry in a few moments, "
            f"or enable Demo Mode in settings to test deterministic local workflows."
        )
        fail_event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "agent_name": "AGENT_ORCHESTRATOR",
            "stage": "api_failure_recovery",
            "task_assigned": "Catch API failure and preserve user state securely",
            "status": "FAILED",
            "tools_consulted": ["resilient_error_handler"],
            "result_summary": f"Sarvam API failure caught safely: {str(api_err)}",
            "duration_ms": round((time.perf_counter() - start_wall) * 1000, 2),
            "validation_status": "BLOCKED",
        }
        trace = list(state.get("agent_execution_trace", []))
        trace.append(fail_event)
        state["agent_execution_trace"] = trace
        state["final_response"] = err_msg
        state["errors"] = [str(api_err)]
        return state
    except Exception as exc:
        logger.exception("Unexpected orchestrator error")
        fail_event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "agent_name": "AGENT_ORCHESTRATOR",
            "stage": "runtime_error_recovery",
            "task_assigned": "Graceful fallback on unexpected system error",
            "status": "FAILED",
            "tools_consulted": ["runtime_exception_guard"],
            "result_summary": f"System error caught: {str(exc)}",
            "duration_ms": round((time.perf_counter() - start_wall) * 1000, 2),
            "validation_status": "BLOCKED",
        }
        trace = list(state.get("agent_execution_trace", []))
        trace.append(fail_event)
        state["agent_execution_trace"] = trace
        state["final_response"] = f"An unexpected error occurred during investigation: {str(exc)}"
        state["errors"] = [str(exc)]
        return state
