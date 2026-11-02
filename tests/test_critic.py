"""Tests for Evidence & Safety Critic Agent and bounded revision loops."""

import pytest
from fitvoice.agents.evidence_critic import EvidenceSafetyCriticAgent


def test_critic_approves_verified_report():
    critic = EvidenceSafetyCriticAgent(max_revisions=2)
    report = {
        "observations": ["Completed 8 sessions"],
        "calculated_metrics": ["Max working weight: 95.0 kg", "Peak Estimated 1RM (Epley): 111.0 kg"],
        "possible_explanations": ["Associated with cumulative sleep debt."],
        "limitations": ["Correlation does not prove causation."],
        "data_sufficiency": "SUFFICIENT",
    }
    analytical = {
        "progression": {"max_weight_lifted_kg": 95.0, "peak_estimated_1rm_kg": 111.0}
    }
    recovery = {"overall_summary": {"average_sleep_hours": 6.5}}

    audit = critic.audit_report(report, analytical, recovery, revision_count=0)
    assert audit["verdict"] == "APPROVED"
    assert audit["critic_output"]["metric_verification_passed"] is True


def test_critic_flags_unsupported_metrics():
    critic = EvidenceSafetyCriticAgent(max_revisions=2)
    report = {
        "observations": ["Completed 8 sessions"],
        # Fabricated number: claims 130 kg instead of 95.0 kg
        "calculated_metrics": ["Max working weight: 130.0 kg"],
        "possible_explanations": ["Fatigue"],
        "limitations": ["Correlation does not prove causation"],
        "data_sufficiency": "SUFFICIENT",
    }
    analytical = {
        "progression": {"max_weight_lifted_kg": 95.0, "peak_estimated_1rm_kg": 111.0}
    }
    recovery = {}

    audit = critic.audit_report(report, analytical, recovery, revision_count=0)
    assert audit["verdict"] == "REQUIRES_REVISION"
    assert len(audit["critic_output"]["unsupported_claims"]) > 0


def test_critic_blocks_medical_diagnoses():
    critic = EvidenceSafetyCriticAgent(max_revisions=2)
    report = {
        "observations": ["Completed sessions"],
        "calculated_metrics": ["Max working weight: 95.0 kg"],
        "possible_explanations": ["Athlete is diagnosed with clinical overtraining syndrome and adrenal fatigue."],
        "limitations": [],
        "data_sufficiency": "SUFFICIENT",
    }
    analytical = {"progression": {"max_weight_lifted_kg": 95.0}}
    recovery = {}

    audit = critic.audit_report(report, analytical, recovery, revision_count=0)
    assert audit["verdict"] == "BLOCKED"
    assert len(audit["critic_output"]["safety_concerns"]) > 0


def test_critic_enforces_bounded_revisions():
    critic = EvidenceSafetyCriticAgent(max_revisions=2)
    report = {
        "observations": ["Completed sessions"],
        "calculated_metrics": ["Max weight unverified"],
        "possible_explanations": ["Stagnant"],
        "limitations": [],
        "data_sufficiency": "SUFFICIENT",
    }
    analytical = {"progression": {"max_weight_lifted_kg": 95.0}}
    recovery = {}

    # When revision_count >= max_revisions, it downgrades rather than looping infinitely
    audit = critic.audit_report(report, analytical, recovery, revision_count=2)
    assert audit["verdict"] == "APPROVED_WITH_CAVEATS"
    assert any("Max revisions (2) reached" in c for c in audit["critic_output"]["feedback_notes"])

