"""Sarvam AI Client integration for Saaras v4 (STT), Sarvam 105B (LLM), and Bulbul (TTS).

Features:
- Bounded exponential backoff retries on transient network/API failures.
- Preserves raw inputs and logs safe error traces.
- Transparent demo / offline mode with deterministic outputs clearly flagged.
- Never pretends demo output is a live inference.
"""

import time
import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from fitvoice.config import settings

logger = logging.getLogger("fitvoice.clients.sarvam")


class SarvamAPIError(Exception):
    """Raised when a Sarvam AI API call fails after bounded retries."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class SarvamClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 35.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key if api_key is not None else settings.sarvam_api_key
        self.base_url = (base_url or settings.sarvam_base_url).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid API key is configured."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "api-subscription-key": self.api_key or "",
            "Authorization": f"Bearer {self.api_key or ''}",
        }
        return headers

    # ---------------------------------------------------------
    # 1. Speech-to-Text: Saaras v4
    # ---------------------------------------------------------
    def speech_to_text(
        self,
        audio_file_path: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        language_code: str = "en-IN",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio using Sarvam Saaras v4."""
        model_name = model or settings.sarvam_stt_model

        # Demo mode or unconfigured API key
        if not self.is_configured or settings.demo_mode:
            logger.info("Using Sarvam Saaras v4 demonstration mode for transcription.")
            return {
                "transcript": "Logged bench press 3 sets of 5 reps at 95 kilograms, felt heavy RPE 9.5.",
                "language_code": language_code,
                "model": f"{model_name}-demo",
                "is_live_inference": False,
            }

        url = f"{self.base_url}/speech-to-text"
        files = {}
        if audio_file_path and os.path.exists(audio_file_path):
            with open(audio_file_path, "rb") as f:
                content = f.read()
            files = {"file": (os.path.basename(audio_file_path), content, "audio/wav")}
        elif audio_bytes:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        else:
            raise ValueError("Either audio_file_path or audio_bytes must be provided for STT.")

        data = {"model": model_name, "language_code": language_code}

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=self._get_headers(), data=data, files=files)
                    if resp.status_code == 200:
                        payload = resp.json()
                        return {
                            "transcript": payload.get("transcript", ""),
                            "language_code": payload.get("language_code", language_code),
                            "model": model_name,
                            "is_live_inference": True,
                        }
                    if resp.status_code in (429, 500, 502, 503, 504):
                        time.sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    raise SarvamAPIError(
                        f"Saaras STT failed with HTTP {resp.status_code}",
                        resp.status_code,
                        resp.text
                    )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                time.sleep(0.5 * (2 ** (attempt - 1)))

        raise SarvamAPIError(f"Saaras STT failed after {self.max_retries} retries: {last_error}")

    # ---------------------------------------------------------
    # 2. LLM Reasoning & Extraction: Sarvam 105B
    # ---------------------------------------------------------
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        model: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invoke Sarvam 105B for structured extraction and multi-agent reasoning."""
        model_name = model or settings.sarvam_llm_model

        if not self.is_configured or settings.demo_mode:
            # Deterministic intelligent simulation based on system prompt / query context
            return self._mock_sarvam_llm_response(messages, model_name)

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = {"type": response_format}

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=self._get_headers(), json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return {
                            "content": content,
                            "model": model_name,
                            "usage": data.get("usage", {}),
                            "is_live_inference": True,
                        }
                    if resp.status_code in (429, 500, 502, 503, 504):
                        last_error = SarvamAPIError(
                            f"HTTP {resp.status_code}: {resp.text}",
                            status_code=resp.status_code,
                            response_text=resp.text,
                        )
                        time.sleep(0.1 * (2 ** (attempt - 1)))
                        continue
                    raise SarvamAPIError(
                        f"Sarvam LLM failed with HTTP {resp.status_code}",
                        resp.status_code,
                        resp.text
                    )
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                time.sleep(0.1 * (2 ** (attempt - 1)))

        status = getattr(last_error, "status_code", None)
        raise SarvamAPIError(
            f"Sarvam LLM request failed after {self.max_retries} retries: {last_error}",
            status_code=status
        )

    # ---------------------------------------------------------
    # 3. Text-to-Speech: Bulbul v2
    # ---------------------------------------------------------
    def text_to_speech(
        self,
        text: str,
        target_language_code: str = "en-IN",
        speaker: str = "priya",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize spoken response using Sarvam Bulbul."""
        model_name = model or settings.sarvam_tts_model

        if not self.is_configured or settings.demo_mode:
            logger.info("Using Sarvam Bulbul demonstration mode for audio synthesis.")
            return {
                "audio_base64": None,
                "text": text,
                "speaker": speaker,
                "model": f"{model_name}-demo",
                "is_live_inference": False,
            }

        url = f"{self.base_url}/text-to-speech"
        payload = {
            "inputs": [text[:500]],  # bounded text
            "target_language_code": target_language_code,
            "speaker": speaker,
            "model": model_name,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._get_headers(), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    audios = data.get("audios", [])
                    return {
                        "audio_base64": audios[0] if audios else None,
                        "text": text,
                        "speaker": speaker,
                        "model": model_name,
                        "is_live_inference": True,
                    }
                raise SarvamAPIError(f"Bulbul TTS failed with HTTP {resp.status_code}", resp.status_code, resp.text)
        except Exception as exc:
            logger.warning(f"TTS synthesis non-critical failure: {exc}")
            return {
                "audio_base64": None,
                "text": text,
                "speaker": speaker,
                "error": str(exc),
                "is_live_inference": False,
            }

    # ---------------------------------------------------------
    # Mock fallback for test reproducibility & offline demo
    # ---------------------------------------------------------
    def _mock_sarvam_llm_response(self, messages: List[Dict[str, str]], model_name: str) -> Dict[str, Any]:
        """Generate structured deterministic outputs when offline or in demo mode."""
        user_msg = messages[-1].get("content", "")
        sys_msg = messages[0].get("content", "") if len(messages) > 1 else ""

        # Default fallback response
        return {
            "content": f"[Simulated Sarvam 105B Output]: Interpreted query '{user_msg[:60]}...'",
            "model": f"{model_name}-demo",
            "usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200},
            "is_live_inference": False,
        }
