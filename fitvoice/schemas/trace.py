"""Schemas for Agent Observability and Execution Traces."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AgentExecutionEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    agent_name: str = Field(..., description="Name of the agent (e.g. PROGRESS_DETECTIVE)")
    stage: str = Field(..., description="Execution stage or workflow step")
    task_assigned: str = Field(..., description="Short explanation of what the agent was tasked to do")
    status: str = Field(..., description="Execution status: STARTED, SUCCESS, REQUIRES_REVISION, BLOCKED, SKIPPED, FAILED")
    tools_consulted: List[str] = Field(default_factory=list, description="Deterministic tools or data sources consulted")
    result_summary: str = Field(..., description="Concise outcome summary without exposing internal raw chain-of-thought")
    duration_ms: float = Field(0.0, description="Duration in milliseconds")
    validation_status: str = Field(
        "NOT_APPLICABLE",
        description="Validation outcome: PENDING, APPROVED, APPROVED_WITH_CAVEATS, REQUIRES_REVISION, BLOCKED, NOT_APPLICABLE"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp"
    )
