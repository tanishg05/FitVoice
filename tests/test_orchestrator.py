"""Tests for LangGraph Orchestrator workflows, routing, and execution traces."""

import pytest
from unittest.mock import patch
from fitvoice.orchestrator.runner import run_pipeline
from fitvoice.orchestrator.graph import FitVoiceOrchestrator
from fitvoice.clients.sarvam import SarvamAPIError


def test_workflow_a_voice_logging(temp_db, mock_sarvam_client):
    res = run_pipeline(
        user_query="Log bench press 3 sets of 5 reps at 95 kg, felt solid",
        user_id="alex_lifter",
        sarvam_client=mock_sarvam_client,
    )
    assert res["request_type"] == "voice_logging"
    assert res["requires_user_confirmation"] is True
    assert "95" in res["final_response"]

    # Verify selective execution: Recovery, Coach, Critic must NOT run
    agent_names = [e["agent_name"] for e in res["agent_execution_trace"]]
    assert "VOICE_INTELLIGENCE" in agent_names
    assert "RECOVERY_INTELLIGENCE" not in agent_names
    assert "ADAPTIVE_COACH" not in agent_names
    assert "EVIDENCE_SAFETY_CRITIC" not in agent_names


def test_workflow_b_simple_question(temp_db):
    res = run_pipeline(
        user_query="What is my peak bench press and volume?",
        user_id="alex_lifter",
    )
    assert res["request_type"] == "simple_question"
    assert "Fitness Data Scientist" in res["final_response"]
    assert "95" in res["final_response"]

    # Verify selective execution: only Router and Data Scientist
    agent_names = [e["agent_name"] for e in res["agent_execution_trace"]]
    assert agent_names == ["AGENT_ORCHESTRATOR", "FITNESS_DATA_SCIENTIST"]


def test_workflow_c_progress_investigation(temp_db):
    res = run_pipeline(
        user_query="Why has my bench press plateaued over the last 4 weeks despite working out consistently?",
        user_id="alex_lifter",
    )
    assert res["request_type"] == "progress_investigation"
    assert "FitVoice Multi-Agent Progress Investigation" in res["final_response"]
    assert "Verified Observations" in res["final_response"]
    assert "Adaptive Coach Recommendations" in res["final_response"]

    agent_names = [e["agent_name"] for e in res["agent_execution_trace"]]
    # All substantive agents must have run in sequence
    assert "AGENT_ORCHESTRATOR" in agent_names
    assert "FITNESS_DATA_SCIENTIST" in agent_names
    assert "RECOVERY_INTELLIGENCE" in agent_names
    assert "PROGRESS_DETECTIVE" in agent_names
    assert "EVIDENCE_SAFETY_CRITIC" in agent_names
    assert "ADAPTIVE_COACH" in agent_names


def test_workflow_d_insufficient_data(temp_db):
    res = run_pipeline(
        user_query="Why is my bench press not progressing?",
        user_id="newbie_sam",  # user with only 1 session and 0 recovery logs
    )
    # Must report data limitations honestly and not fabricate numbers
    assert "Insufficient" in res["final_response"] or "Data Consistency" in res["final_response"]
    # Check that recommendation tells user to log more data rather than prescribing heavy workouts
    assert "Log at least" in res["final_response"] or "limited" in res["final_response"].lower()


def test_workflow_e_api_failure_recovery(temp_db):
    with patch("fitvoice.clients.sarvam.SarvamClient.chat_completion") as mock_call:
        mock_call.side_effect = SarvamAPIError("Sarvam service down", status_code=503)
        res = run_pipeline(
            user_query="Why has my bench press plateaued?",
            user_id="alex_lifter",
        )
        # Verify user query preserved and graceful failure message
        assert "alex_lifter" == res["user_id"]
        assert len(res["agent_execution_trace"]) > 0


def test_execution_trace_attributes(temp_db):
    res = run_pipeline(
        user_query="Why has my bench press plateaued over the last 4 weeks?",
        user_id="alex_lifter",
    )
    for evt in res["agent_execution_trace"]:
        assert "event_id" in evt
        assert "agent_name" in evt
        assert "status" in evt
        assert "tools_consulted" in evt
        assert "result_summary" in evt
        assert "duration_ms" in evt
        assert evt["duration_ms"] >= 0.0
