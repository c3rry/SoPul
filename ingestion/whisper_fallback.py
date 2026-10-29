"""Pulse2026 Whisper Fallback Audio Transcriber (Ephemeral, Zero Persistent Media)."""

import asyncio
import os
import tempfile

from yt_dlp import YoutubeDL


class EphemeralWhisperTranscriber:
    """Ephemeral audio transcription via faster-whisper with guaranteed cleanup."""

    def __init__(self, model_size: str = "base.en"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        """Lazy load the faster-whisper model."""
        if self._model is None:
            import torch
            from faster_whisper import WhisperModel

            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            self._model = WhisperModel(self.model_size, device=device, compute_type=compute_type)
        return self._model

    def transcribe_url(self, video_url: str) -> str:
        """Download ephemeral audio to temporary file, transcribe, and immediately delete."""
        temp_audio_path = None
        try:
            # Create a unique cross-platform temporary file
            with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
                temp_audio_path = tmp.name

            ydl_opts = {
                "format": "worstaudio/worst",
                "outtmpl": temp_audio_path,
                "overwrites": True,
                "quiet": True,
                "no_warnings": True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
                return ""

            model = self._get_model()
            segments, _ = model.transcribe(temp_audio_path, language="en", beam_size=1)
            transcript_text = " ".join(segment.text.strip() for segment in segments)
            return transcript_text.strip()

        except Exception:
            return ""
        finally:
            # Crucial invariant: never retain audio files on disk
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except OSError:
                    pass

    async def transcribe_url_async(self, video_url: str) -> str:
        """Asynchronous wrapper for transcribe_url."""
        return await asyncio.to_thread(self.transcribe_url, video_url)
