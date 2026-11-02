"""Request classification and routing for FitVoice Orchestrator."""

import re
from typing import Dict, Any


def classify_request(state: Dict[str, Any]) -> str:
    """Classify the incoming query into one of the designated FitVoice workflows."""
    user_query = state.get("user_query", "").strip().lower()
    raw_audio = state.get("raw_audio_path")

    # If raw audio is supplied, it is primarily a voice logging or spoken inquiry
    if raw_audio:
        if any(w in user_query for w in ["plateau", "stuck", "why", "progress", "analyze", "trend"]):
            return "progress_investigation"
        return "voice_logging"

    # Explicit logging keywords
    logging_keywords = [
        "log", "logged", "record", "recorded", "ate", "had", "slept", "soya", "khaya",
        "did 3 sets", "did 4 sets", "reps at", "reps @", "rpe", "kilo", "kg"
    ]
    # Check if this matches a logging statement (e.g. "Bench press 3 sets of 5 reps at 95kg")
    if any(k in user_query for k in ["sets of", "sets at", "set 5 rep", "hrs sleep", "hours of sleep"]):
        return "voice_logging"
    if any(user_query.startswith(k) for k in ["log", "record", "i did", "maine"]):
        return "voice_logging"

    # Investigation & Plateau keywords
    investigation_keywords = [
        "why", "plateau", "plateaued", "stuck", "stalled", "not progressing",
        "investigate", "progress", "trend", "breakdown", "analysis", "compare",
        "why has my", "explain my", "fatigue", "recovery"
    ]
    if any(k in user_query for k in investigation_keywords):
        return "progress_investigation"

    # Simple factual fitness questions
    simple_question_keywords = [
        "what is my", "max", "highest", "pr", "personal record", "how many",
        "volume", "last workout", "yesterday", "summary", "1rm", "estimated 1rm"
    ]
    if any(k in user_query for k in simple_question_keywords):
        return "simple_question"

    # Default fallback
    return "progress_investigation" if len(user_query) > 30 else "simple_question"

