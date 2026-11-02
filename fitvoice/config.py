"""Configuration settings for FitVoice Multi-Agent System."""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    # Sarvam AI Credentials & Endpoints
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
    sarvam_base_url: str = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
    sarvam_llm_model: str = os.getenv("SARVAM_LLM_MODEL", "sarvam-105b")
    sarvam_stt_model: str = os.getenv("SARVAM_STT_MODEL", "saaras:v4")
    sarvam_tts_model: str = os.getenv("SARVAM_TTS_MODEL", "bulbul:v2")

    # System Configuration
    demo_mode: bool = os.getenv("FITVOICE_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    db_path: str = os.getenv("FITVOICE_DB_PATH", str(BASE_DIR / "fitvoice.db"))
    max_revisions: int = int(os.getenv("FITVOICE_MAX_REVISIONS", "2"))
    execution_timeout_seconds: int = int(os.getenv("FITVOICE_EXECUTION_TIMEOUT_SECONDS", "30"))
    environment: str = os.getenv("FITVOICE_ENV", "development")

    @property
    def has_live_sarvam_api(self) -> bool:
        return bool(self.sarvam_api_key and self.sarvam_api_key.strip() and not self.sarvam_api_key.startswith("your_"))


settings = Settings()
