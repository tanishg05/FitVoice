"""Tests for individual agent execution contracts and schemas."""

import pytest
from fitvoice.agents.voice_intelligence import VoiceIntelligenceAgent
from fitvoice.agents.data_scientist import FitnessDataScientistAgent
from fitvoice.agents.recovery_intelligence import RecoveryIntelligenceAgent
from fitvoice.agents.progress_detective import ProgressDetectiveAgent
from fitvoice.agents.adaptive_coach import AdaptiveCoachAgent


def test_voice_intelligence_agent(mock_sarvam_client):
    agent = VoiceIntelligenceAgent(sarvam_client=mock_sarvam_client)
    res = agent.process(
        user_query="Logged bench press 3 sets of 5 reps at 95 kg, felt RPE 9",
        user_id="test_user",
    )
    assert res["requires_user_confirmation"] is True
    candidates = res["candidate_records"]
    assert len(candidates["workout_candidates"]) == 1
    w = candidates["workout_candidates"][0]
    assert w["session_name"] == "Bench Press Session"
    assert len(w["sets"]) == 3
    assert w["sets"][0]["weight_kg"] == 95.0
    assert w["sets"][0]["reps"] == 5
    assert w["sets"][0]["rpe"] == 9.0
    # Trace event verification
    assert res["trace_event"]["agent_name"] == "VOICE_INTELLIGENCE"
    assert res["trace_event"]["status"] == "SUCCESS"


def test_data_scientist_agent(repository):
    agent = FitnessDataScientistAgent(repository=repository)
    res = agent.process(user_id="alex_lifter", exercise_name="Bench Press", days_back=28)
    prog = res["progression"]
    assert prog["total_sets"] == 28
    assert prog["max_weight_lifted_kg"] == 95.0
    assert len(prog["source_record_ids"]) == 28
    assert res["comparison"]["is_plateau_detected"] is True
    assert res["trace_event"]["status"] == "SUCCESS"


def test_recovery_intelligence_agent(repository):
    agent = RecoveryIntelligenceAgent(repository=repository)
    res = agent.process(user_id="alex_lifter", days_back=28)
    assert res["sufficiency"]["sufficiency_status"] == "SUFFICIENT"
    assert res["overall_summary"]["average_sleep_hours"] > 5.0
    assert len(res["observed_associations"]) > 0
    # Strict guardrail: limitations present
    assert len(res["limitations"]) > 0


def test_progress_detective_agent():
    agent = ProgressDetectiveAgent()
    plan = agent.generate_plan("Why has my bench press plateaued?", "alex_lifter")
    assert plan["target_exercise"] == "Bench Press"
    assert "workout_sessions" in plan["datasets_needed"]

    mock_workout = {
        "progression": {
            "exercise": "Bench Press",
            "total_sessions": 8,
            "total_sets": 28,
            "max_weight_lifted_kg": 95.0,
            "peak_estimated_1rm_kg": 111.0,
            "total_volume_kg": 14645.0,
        },
        "comparison": {"is_plateau_detected": True, "e1rm_percent_change": -0.15},
    }
    mock_recovery = {
        "sufficiency": {"sufficiency_status": "SUFFICIENT"},
        "overall_summary": {"total_logs": 28, "average_sleep_hours": 6.5, "average_soreness": 5.0},
        "comparison": {"sleep_delta_hours": -2.2, "soreness_delta": 3.0},
    }

    report_res = agent.synthesize_report(plan, mock_workout, mock_recovery)
    rep = report_res["report"]
    assert len(rep["observations"]) > 0
    assert len(rep["calculated_metrics"]) > 0
    assert len(rep["possible_explanations"]) > 0
    assert len(rep["limitations"]) > 0
    assert report_res["trace_event"]["agent_name"] == "PROGRESS_DETECTIVE"


def test_adaptive_coach_agent():
    agent = AdaptiveCoachAgent()
    mock_report = {
        "observations": ["8 sessions logged"],
        "calculated_metrics": ["Max weight: 95 kg", "Sleep fell by 2.2 hrs"],
        "data_sufficiency": "SUFFICIENT",
    }
    res = agent.formulate_recommendations(
        user_query="Why am I stuck at 95kg bench?",
        user_id="alex_lifter",
        validated_report=mock_report,
        critic_verdict="APPROVED",
    )
    steps = res["actionable_steps"]
    assert len(steps) >= 3
    # Check that deload and recovery protocols exist
    assert any("deload" in s["action"].lower() for s in steps)
    assert any("sleep" in s["action"].lower() for s in steps)
    # Check evidence grounding
    assert all(s["grounded_in_record"] for s in steps)
    assert "medical_disclaimer" in res["coach_output"]

