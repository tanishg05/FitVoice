"""FitVoice Specialized Agents Module."""

from fitvoice.agents.base import BaseAgent
from fitvoice.agents.voice_intelligence import VoiceIntelligenceAgent
from fitvoice.agents.data_scientist import FitnessDataScientistAgent
from fitvoice.agents.recovery_intelligence import RecoveryIntelligenceAgent
from fitvoice.agents.progress_detective import ProgressDetectiveAgent
from fitvoice.agents.evidence_critic import EvidenceSafetyCriticAgent
from fitvoice.agents.adaptive_coach import AdaptiveCoachAgent

__all__ = [
    "BaseAgent",
    "VoiceIntelligenceAgent",
    "FitnessDataScientistAgent",
    "RecoveryIntelligenceAgent",
    "ProgressDetectiveAgent",
    "EvidenceSafetyCriticAgent",
    "AdaptiveCoachAgent",
]

