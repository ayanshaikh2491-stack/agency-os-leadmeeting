"""SBA Translation Engine — Live meeting translation + transcription + summary.

No extra API cost. Uses SBA's existing LLM for everything.

Translation Flow:
  Client (English/other) → translate_for_owner() → Hinglish (aapko dikhe)
  Aap (Hinglish) → translate_for_client() → English/other (client ko jaye)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import openai
from admin.config import settings

logger = logging.getLogger(__name__)


class SBATranslationEngine:
    """Translate meeting conversations in real-time + transcribe + summarize."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(
            api_key=settings.WORKSPACE_API_KEY or None,
            base_url=settings.WORKSPACE_API_BASE or None,
        )
        self._model = settings.WORKSPACE_AGENT_MODEL

    async def translate_for_owner(
        self,
        text: str,
        source_lang: str = "English",
    ) -> str:
        """Translate client's message to Hinglish for the owner.

        Client English bole → Aapko Hinglish mein dikhe.
        """
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a real-time meeting translator. "
                        f"Translate the following {source_lang} text to Hinglish "
                        "(Hindi + Urdu + English mix, natural conversational tone). "
                        "Output ONLY the translation, no explanations or quotes."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return resp.choices[0].message.content or text

    async def translate_for_client(
        self,
        text: str,
        target_lang: str = "English",
    ) -> str:
        """Translate owner's Hinglish to professional English for the client."""
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Translate this Hinglish message to professional {target_lang}. "
                        "Keep it polite and business-appropriate. "
                        "Output ONLY the translation."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return resp.choices[0].message.content or text

    async def transcribe_audio(self, audio_path: str) -> list[dict[str, Any]]:
        """Transcribe an audio file to text segments using LLM vision.

        Args:
            audio_path: Path to audio file.

        Returns: List of {speaker, text, timestamp} segments.
        """
        import base64
        try:
            with open(audio_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode()

            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Transcribe this meeting audio to text. "
                            "Identify different speakers if possible. "
                            "Output JSON array: "
                            '[{"speaker": "Client/Owner/Unknown", '
                            '"text": "...", '
                            '"timestamp": "MM:SS"}]'
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio_url",
                                "audio_url": {"url": f"data:audio/wav;base64,{audio_b64}"},
                            }
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            text = resp.choices[0].message.content or "[]"
            # Clean markdown code fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                text = text.rsplit("```", 1)[0]
            return json.loads(text.strip())
        except Exception as exc:
            logger.exception("Transcription failed: %s", exc)
            return [{"speaker": "Unknown", "text": "[Transcription failed]", "timestamp": "00:00"}]

    async def generate_summary(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate structured meeting summary from transcript segments.

        Returns:
          - key_points: list of key discussion points
          - action_items: list of action items with owner
          - decisions: list of decisions made
          - next_steps: list of next steps
          - full_summary: narrative summary in Hinglish
        """
        transcript_text = "\n".join(
            f"[{s.get('timestamp', '')}] {s.get('speaker', '?')}: {s.get('text', '')}"
            for s in segments
        )

        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are SBA's meeting analyst. Summarize this meeting transcript. "
                        "Respond in JSON only with keys: "
                        "key_points (list), action_items (list of {task, owner, deadline}), "
                        "decisions (list), next_steps (list), "
                        "full_summary (str — detailed Hinglish summary for the owner)"
                    ),
                },
                {
                    "role": "user",
                    "content": transcript_text[:8000],
                },
            ],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or "{}"
        return json.loads(text)

    async def translate_meeting_live(
        self,
        segments: list[dict[str, Any]],
        owner_name: str = "Aap",
    ) -> list[dict[str, Any]]:
        """Translate an entire meeting transcript in one pass.

        Each segment gets translated based on speaker:
          - Client → Hinglish (owner ke liye)
          - Owner → English (client ke liye)

        Returns: Segments with added 'translation' key.
        """
        result = []
        for seg in segments:
            speaker = seg.get("speaker", "").lower()
            text = seg.get("text", "")

            if "client" in speaker or "lead" in speaker:
                translation = await self.translate_for_owner(text)
            else:
                translation = await self.translate_for_client(text)

            seg["translation"] = translation
            result.append(seg)

        return result
