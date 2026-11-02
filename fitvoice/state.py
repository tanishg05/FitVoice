"""Shared typed state for the FitVoice LangGraph Multi-Agent Orchestrator."""

from typing import TypedDict, List, Dict, Any, Optional
import uuid


class FitVoiceState(TypedDict, total=False):
    # Request Identifiers & Context
    request_id: str
    user_id: str
    user_query: str
    preferred_language: str
    request_type: str  # 'voice_logging', 'simple_question', 'progress_investigation', 'insufficient_data', 'api_failure'

    # Audio & Voice Input
    raw_audio_path: Optional[str]
    transcript: Optional[str]

    # Voice Intelligence & Record Confirmation
    candidate_records: List[Dict[str, Any]]
    confirmed_record_ids: List[str]
    requires_user_confirmation: bool
    confirmation_prompt: Optional[str]

    # Investigation & Data Science Context
    analysis_period: Dict[str, Any]
    investigation_plan: Dict[str, Any]
    retrieved_workout_data: List[Dict[str, Any]]
    retrieved_recovery_data: List[Dict[str, Any]]
    analytical_results: Dict[str, Any]

    # Agent Findings
    progress_findings: Dict[str, Any]
    recovery_findings: Dict[str, Any]
    proposed_recommendations: Dict[str, Any]

    # Quality Control & Critic Loop
    critic_verdict: str  # 'APPROVED', 'APPROVED_WITH_CAVEATS', 'REQUIRES_REVISION', 'BLOCKED'
    critic_feedback: List[str]
    revision_count: int

    # Agent Observability & Audit Trail
    agent_execution_trace: List[Dict[str, Any]]

    # Final Output & Speech
    final_response: str
    response_audio_reference: Optional[str]
    errors: List[str]


def create_initial_state(
    user_query: str,
    user_id: str = "demo_athlete",
    preferred_language: str = "en-IN",
    raw_audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
) -> FitVoiceState:
    """Create a pristine initial state with safe defaults."""
    return FitVoiceState(
        request_id=f"req_{uuid.uuid4().hex[:10]}",
        user_id=user_id,
        user_query=user_query,
        preferred_language=preferred_language,
        request_type="",
        raw_audio_path=raw_audio_path,
        transcript=transcript,
        candidate_records=[],
        confirmed_record_ids=[],
        requires_user_confirmation=False,
        confirmation_prompt=None,
        analysis_period={},
        investigation_plan={},
        retrieved_workout_data=[],
        retrieved_recovery_data=[],
        analytical_results={},
        progress_findings={},
        recovery_findings={},
        proposed_recommendations={},
        critic_verdict="PENDING",
        critic_feedback=[],
        revision_count=0,
        agent_execution_trace=[],
        final_response="",
        response_audio_reference=None,
        errors=[],
    )
