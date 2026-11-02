"""Typed contracts (input/output schemas) for all 6 specialized agents."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# 1. Voice Intelligence Agent Contracts
# ---------------------------------------------------------
class VoiceIntelligenceInput(BaseModel):
    user_id: str
    user_query: str
    transcript: Optional[str] = None
    preferred_language: str = "en-IN"


class ExtractedWorkoutCandidate(BaseModel):
    session_name: str
    date: str
    sets: List[Dict[str, Any]]
    duration_minutes: Optional[int] = None
    confidence: float = 1.0


class ExtractedNutritionCandidate(BaseModel):
    date: str
    item: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    confidence: float = 1.0


class ExtractedRecoveryCandidate(BaseModel):
    date: str
    sleep_hours: float
    soreness_score: Optional[int] = None
    energy_score: Optional[int] = None
    notes: Optional[str] = None


class VoiceIntelligenceOutput(BaseModel):
    workout_candidates: List[ExtractedWorkoutCandidate] = Field(default_factory=list)
    nutrition_candidates: List[ExtractedNutritionCandidate] = Field(default_factory=list)
    recovery_candidates: List[ExtractedRecoveryCandidate] = Field(default_factory=list)
    ambiguities_found: List[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None
    requires_user_confirmation: bool = True
    review_summary: str = Field(..., description="Human-readable review text for the user before confirmation")


# ---------------------------------------------------------
# 2. Fitness Data Scientist Agent Contracts
# ---------------------------------------------------------
class DataScientistInput(BaseModel):
    user_id: str
    exercise_name: Optional[str] = None
    analysis_period_days: int = 28
    metric_requests: List[str] = Field(
        default_factory=lambda: ["volume_load", "estimated_1rm", "frequency", "personal_records"]
    )


class MetricCalculation(BaseModel):
    period: str
    metric: str
    value: float
    unit: str
    source_record_ids: List[str]
    notes: Optional[str] = None


class DataScientistOutput(BaseModel):
    exercise_name: Optional[str] = None
    period_start: str
    period_end: str
    metrics: List[MetricCalculation] = Field(default_factory=list)
    volume_progression: Dict[str, Any] = Field(default_factory=dict)
    estimated_1rm_progression: Dict[str, Any] = Field(default_factory=dict)
    weekly_frequency: Dict[str, int] = Field(default_factory=dict)
    personal_records: List[Dict[str, Any]] = Field(default_factory=list)
    missing_observations_count: int = 0
    data_quality_flags: List[str] = Field(default_factory=list)
    total_records_analyzed: int = 0


# ---------------------------------------------------------
# 3. Recovery Intelligence Agent Contracts
# ---------------------------------------------------------
class RecoveryIntelligenceInput(BaseModel):
    user_id: str
    period_start: str
    period_end: str
    workout_dates: List[str] = Field(default_factory=list)


class RecoveryIntelligenceOutput(BaseModel):
    period_start: str
    period_end: str
    total_recovery_days_logged: int
    missing_recovery_days: int
    data_sufficiency: Literal["SUFFICIENT", "PARTIAL", "INSUFFICIENT"]
    average_sleep_hours: Optional[float] = None
    sleep_trend: Optional[str] = None
    average_soreness: Optional[float] = None
    average_energy: Optional[float] = None
    observed_associations: List[str] = Field(
        default_factory=list,
        description="Tentative correlations observed between recovery indicators and training days"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Safety and physiological caveats (e.g., sleep duration does not equal sleep architecture)"
    )


# ---------------------------------------------------------
# 4. Progress Detective Agent Contracts
# ---------------------------------------------------------
class ProgressDetectiveInput(BaseModel):
    user_id: str
    user_query: str
    preferred_language: str = "en-IN"


class InvestigationReport(BaseModel):
    investigation_question: str
    datasets_consulted: List[str] = Field(default_factory=list)
    observations: List[str] = Field(
        default_factory=list,
        description="Raw logged facts from verified records"
    )
    calculated_metrics: List[str] = Field(
        default_factory=list,
        description="Exact numerical outputs from Data Scientist tools with units"
    )
    possible_explanations: List[str] = Field(
        default_factory=list,
        description="Hypotheses supported by data (e.g. fatigue accumulation, volume stagnation)"
    )
    alternative_interpretations: List[str] = Field(
        default_factory=list,
        description="Plausible competing factors (e.g. life stress, nutrition tracking gaps)"
    )
    preliminary_recommendations: List[str] = Field(
        default_factory=list,
        description="High-level areas for Adaptive Coach to target"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit gaps in available data, lack of causal proof"
    )
    data_sufficiency: Literal["SUFFICIENT", "PARTIAL", "INSUFFICIENT"] = "SUFFICIENT"


# ---------------------------------------------------------
# 5. Evidence & Safety Critic Agent Contracts
# ---------------------------------------------------------
class EvidenceCriticInput(BaseModel):
    investigation_report: Dict[str, Any]
    deterministic_metrics: List[Dict[str, Any]]
    recovery_findings: Dict[str, Any]
    proposed_recommendations: Optional[List[str]] = None
    revision_count: int = 0


class EvidenceCriticOutput(BaseModel):
    verdict: Literal["APPROVED", "APPROVED_WITH_CAVEATS", "REQUIRES_REVISION", "BLOCKED"]
    metric_verification_passed: bool
    unsupported_claims: List[str] = Field(default_factory=list)
    causality_violations: List[str] = Field(default_factory=list)
    safety_concerns: List[str] = Field(default_factory=list)
    feedback_notes: List[str] = Field(default_factory=list)
    required_revisions: List[str] = Field(default_factory=list)


# ---------------------------------------------------------
# 6. Adaptive Coach Agent Contracts
# ---------------------------------------------------------
class AdaptiveCoachInput(BaseModel):
    user_id: str
    user_query: str
    validated_report: Dict[str, Any]
    critic_verdict: str
    critic_caveats: List[str] = Field(default_factory=list)
    user_experience_level: str = "intermediate"
    training_days_per_week: int = 4


class ActionableStep(BaseModel):
    area: str  # Training, Recovery, Logging
    action: str
    justification: str
    grounded_in_record: str


class AdaptiveCoachOutput(BaseModel):
    summary_message: str
    actionable_steps: List[ActionableStep] = Field(default_factory=list)
    recovery_protocols: List[str] = Field(default_factory=list)
    constraints_respected: List[str] = Field(default_factory=list)
    medical_disclaimer: str = (
        "Recommendations are based on logged training patterns and are not a substitute "
        "for qualified sports medicine or clinical consultation."
    )
    suggest_professional_help: bool = False

