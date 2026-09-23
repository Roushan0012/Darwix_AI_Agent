"""
Unified Web Server for Darwix AI.
Serves:
1. /call    - Interactive Knowledge-Grounded Voice Calling Interface (Question 1)
2. /nudges  - Real-Time Live Audio Streaming Nudges Dashboard (Question 4)
3. /api/kb  - Knowledge Base Hybrid Search API (Question 2)
4. /recordings/{file} - Synthesized Audio Streamer
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.voice.agent import VoiceAgent
from src.voice.audio_service import AudioService
from src.kb.store import KnowledgeStore
from src.kb.schema import SearchResult, KBRecord
from src.real_time.streamer import RealTimePipeline

app = FastAPI(
    title="Darwix AI — Unified Production System",
    description="Knowledge-grounded voice agent, hybrid RAG, and real-time audio nudge dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
agent: Optional[VoiceAgent] = None
audio_service: Optional[AudioService] = None
store: Optional[KnowledgeStore] = None
realtime_pipeline = RealTimePipeline()

class TurnRequest(BaseModel):
    session_id: Optional[str] = None
    text: str

class TurnResponse(BaseModel):
    session_id: str
    user_transcript: Optional[str] = None
    bot_response: str
    audio_url: Optional[str] = None
    status: str
    escalated: bool
    citations_used: List[str]
    lead_data: Dict[str, Any]

class ChunkPayload(BaseModel):
    speaker: str
    text: str

@app.on_event("startup")
def startup():
    global agent, audio_service, store
    kb_path = os.path.join("data", "processed", "knowledge_base.json")
    if not os.path.exists(kb_path):
        from src.kb.parser import DocumentParser
        DocumentParser().ingest_all()

    store = KnowledgeStore.load_from_processed(kb_path)
    agent = VoiceAgent(kb_store=store)
    audio_service = AudioService(output_dir="recordings")
    print("Darwix AI Unified Server ready on port 8000.")

@app.get("/")
def root():
    return RedirectResponse(url="/call")

# --- QUESTION 1: WEB CALLING INTERFACE ---
@app.get("/call", response_class=HTMLResponse)
def get_web_calling_interface():
    html_path = Path("src/voice/web_interface.html")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Web interface not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/voice/turn", response_model=TurnResponse)
async def handle_voice_turn(turn: TurnRequest):
    global agent, audio_service
    if not agent or not audio_service:
        raise HTTPException(status_code=503, detail="Agent initializing")

    try:
        result = agent.process_turn(user_text=turn.text, session_id=turn.session_id)
        audio_filename = f"resp_{result['session_id']}_{os.urandom(4).hex()}.mp3"
        await audio_service.synthesize_speech_async(
            text=result["bot_response"],
            output_filename=audio_filename,
            language="en"
        )
        return TurnResponse(
            session_id=result["session_id"],
            user_transcript=turn.text,
            bot_response=result["bot_response"],
            audio_url=f"/recordings/{audio_filename}",
            status=result["status"],
            escalated=result["escalated"],
            citations_used=result["citations_used"],
            lead_data=result["lead_data"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/audio_turn", response_model=TurnResponse)
async def handle_audio_turn(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Receives live microphone audio from the browser, transcribes it via Groq Whisper,
    and runs the voice agent dialogue turn.
    """
    global agent, audio_service
    if not agent or not audio_service:
        raise HTTPException(status_code=503, detail="Agent initializing")

    temp_path = Path("recordings") / f"upload_{os.urandom(4).hex()}_{audio_file.filename or 'audio.webm'}"
    try:
        with open(temp_path, "wb") as f:
            f.write(await audio_file.read())

        # Transcribe with Groq Whisper
        user_transcript = audio_service.transcribe_audio(temp_path)
        if not user_transcript or len(user_transcript.strip()) == 0:
            user_transcript = "Hello"

        # Process turn with Voice Agent
        result = agent.process_turn(user_text=user_transcript, session_id=session_id)

        # Synthesize agent response
        audio_filename = f"resp_{result['session_id']}_{os.urandom(4).hex()}.mp3"
        await audio_service.synthesize_speech_async(
            text=result["bot_response"],
            output_filename=audio_filename,
            language="en"
        )

        return TurnResponse(
            session_id=result["session_id"],
            user_transcript=user_transcript,
            bot_response=result["bot_response"],
            audio_url=f"/recordings/{audio_filename}",
            status=result["status"],
            escalated=result["escalated"],
            citations_used=result["citations_used"],
            lead_data=result["lead_data"]
        )
    except Exception as e:
        print(f"Error in audio_turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            try: temp_path.unlink()
            except: pass

# --- QUESTION 4: REAL-TIME NUDGE DASHBOARD ---
@app.get("/nudges", response_class=HTMLResponse)
def get_nudges_dashboard():
    html_path = Path("src/real_time/dashboard.html")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/realtime/process_chunk")
def process_audio_chunk(payload: ChunkPayload):
    result = realtime_pipeline.process_chunk(speaker=payload.speaker, text=payload.text)
    result["latency_summary"] = realtime_pipeline.latency_tracker.get_summary()
    return result

@app.get("/api/realtime/latency")
def get_latency_report():
    return realtime_pipeline.latency_tracker.get_summary()

@app.get("/api/realtime/quality")
def get_quality_metrics():
    return realtime_pipeline.nudge_controller.get_quality_metrics()

# --- QUESTION 2: KNOWLEDGE BASE SEARCH ---
@app.get("/api/kb/search", response_model=List[SearchResult])
def search_knowledge_base(query: str = Query(...), top_k: int = 3):
    global store
    if not store:
        raise HTTPException(status_code=503, detail="Store initializing")
    return store.search(query=query, top_k=top_k)

# --- AUDIO STATIC FILE SERVING ---
@app.get("/recordings/{filename}")
def get_recording(filename: str):
    filepath = Path("recordings") / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
