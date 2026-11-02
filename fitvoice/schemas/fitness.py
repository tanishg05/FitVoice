"""Fitness and health record schemas."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class WorkoutSet(BaseModel):
    exercise: str
    weight_kg: float
    reps: int
    rpe: Optional[float] = None
    notes: Optional[str] = None


class WorkoutSessionRecord(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: str
    session_name: str
    sets: List[WorkoutSet] = Field(default_factory=list)
    duration_minutes: Optional[int] = None
    status: Literal["CANDIDATE", "CONFIRMED"] = "CANDIDATE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NutritionRecord(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: str
    item: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    status: Literal["CANDIDATE", "CONFIRMED"] = "CANDIDATE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RecoveryRecord(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: str
    sleep_hours: float
    soreness_score: Optional[int] = Field(None, ge=1, le=10, description="1 (none) to 10 (extreme)")
    energy_score: Optional[int] = Field(None, ge=1, le=10, description="1 (exhausted) to 10 (peak)")
    readiness_score: Optional[int] = Field(None, ge=1, le=10, description="1 (poor) to 10 (ready)")
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MeasurementRecord(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: str
    metric_name: str
    value: float
    unit: str
    status: Literal["CANDIDATE", "CONFIRMED"] = "CANDIDATE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

