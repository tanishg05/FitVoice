"""Base agent definition and execution contract."""

import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fitvoice.schemas.trace import AgentExecutionEvent


class BaseAgent:
    def __init__(
        self,
        name: str,
        role_description: str,
        allowed_tools: Optional[List[str]] = None,
        execution_budget_seconds: float = 10.0,
    ):
        self.name = name
        self.role_description = role_description
        self.allowed_tools = allowed_tools or []
        self.execution_budget_seconds = execution_budget_seconds

    def create_trace_event(
        self,
        task_assigned: str,
        status: str,
        result_summary: str,
        duration_ms: float,
        tools_consulted: Optional[List[str]] = None,
        validation_status: str = "NOT_APPLICABLE",
    ) -> Dict[str, Any]:
        """Generate a typed observable execution event."""
        event = AgentExecutionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            agent_name=self.name,
            stage=self.name.lower(),
            task_assigned=task_assigned,
            status=status,
            tools_consulted=tools_consulted or self.allowed_tools,
            result_summary=result_summary,
            duration_ms=round(duration_ms, 2),
            validation_status=validation_status,
        )
        return event.model_dump()
