"""FitVoice schema package."""

from fitvoice.schemas.fitness import (
    WorkoutSet,
    WorkoutSessionRecord,
    NutritionRecord,
    RecoveryRecord,
    MeasurementRecord,
)
from fitvoice.schemas.trace import AgentExecutionEvent
from fitvoice.schemas.agent_contracts import (
    VoiceIntelligenceInput,
    VoiceIntelligenceOutput,
    DataScientistInput,
    DataScientistOutput,
    RecoveryIntelligenceInput,
    RecoveryIntelligenceOutput,
    ProgressDetectiveInput,
    InvestigationReport,
    EvidenceCriticInput,
    EvidenceCriticOutput,
    AdaptiveCoachInput,
    AdaptiveCoachOutput,
)

__all__ = [
    "WorkoutSet",
    "WorkoutSessionRecord",
    "NutritionRecord",
    "RecoveryRecord",
    "MeasurementRecord",
    "AgentExecutionEvent",
    "VoiceIntelligenceInput",
    "VoiceIntelligenceOutput",
    "DataScientistInput",
    "DataScientistOutput",
    "RecoveryIntelligenceInput",
    "RecoveryIntelligenceOutput",
    "ProgressDetectiveInput",
    "InvestigationReport",
    "EvidenceCriticInput",
    "EvidenceCriticOutput",
    "AdaptiveCoachInput",
    "AdaptiveCoachOutput",
]

