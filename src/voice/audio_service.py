"""
Audio Processing & Speech Pipeline.
Provides neural Text-to-Speech (edge-tts) and high-speed Speech-to-Text (Groq Whisper-large-v3-turbo).
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import edge_tts
from groq import Groq

load_dotenv()

VOICE_MAP = {
    "en": "en-US-AndrewNeural",
    "fil": "fil-PH-AngeloNeural",
    "id": "id-ID-ArdiNeural"
}

class AudioService:
    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.api_key) if self.api_key else None

    async def synthesize_speech_async(
        self,
        text: str,
        output_filename: str,
        language: str = "en"
    ) -> Path:
        """
        Synthesizes spoken audio from text using neural voices.
        """
        voice = VOICE_MAP.get(language, "en-US-AndrewNeural")
        filepath = self.output_dir / output_filename
        
        # Clean markdown characters for voice synthesis
        clean_text = text.replace("**", "").replace("*", "").replace("#", "").strip()
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(str(filepath))
        return filepath

    def synthesize_speech(
        self,
        text: str,
        output_filename: str,
        language: str = "en"
    ) -> Path:
        """Synchronous wrapper for synthesize_speech_async."""
        return asyncio.run(self.synthesize_speech_async(text, output_filename, language))

    def transcribe_audio(self, audio_filepath: Path, language: Optional[str] = None) -> str:
        """
        Transcribes speech audio using Groq Whisper Large v3 Turbo.
        """
        if not self.groq_client:
            raise ValueError("Groq client not initialized. GROQ_API_KEY is required.")

        with open(audio_filepath, "rb") as audio_file:
            kwargs = {
                "file": (audio_filepath.name, audio_file),
                "model": "whisper-large-v3-turbo",
                "response_format": "text"
            }
            if language:
                kwargs["language"] = language

            transcription = self.groq_client.audio.transcriptions.create(**kwargs)
            return str(transcription).strip()

if __name__ == "__main__":
    audio = AudioService()
    print("Testing AudioService Text-to-Speech...")
    path = audio.synthesize_speech("Welcome to Darwix Capital. How can I help your business today?", "test_welcome.mp3")
    print(f"Generated test audio at: {path} (Size: {path.stat().st_size} bytes)")
