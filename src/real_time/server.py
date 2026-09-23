"""
Real-Time Nudge Streaming Server.
Serves interactive Co-pilot dashboard and real-time chunk ingestion endpoint.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.real_time.streamer import RealTimePipeline

app = FastAPI(
    title="Darwix Live — Real-Time Streaming Audio Nudge Service",
    description="Live stream analysis, signal extraction, false-positive suppression, and latency metrics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = RealTimePipeline()

class ChunkPayload(BaseModel):
    speaker: str
    text: str

@app.get("/nudges", response_class=HTMLResponse)
def get_dashboard():
    html_path = Path("src/real_time/dashboard.html")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/realtime/process_chunk")
def process_audio_chunk(payload: ChunkPayload):
    result = pipeline.process_chunk(speaker=payload.speaker, text=payload.text)
    result["latency_summary"] = pipeline.latency_tracker.get_summary()
    return result

@app.get("/api/realtime/latency")
def get_latency_report():
    return pipeline.latency_tracker.get_summary()

@app.get("/api/realtime/quality")
def get_quality_metrics():
    return pipeline.nudge_controller.get_quality_metrics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.real_time.server:app", host="0.0.0.0", port=8001, reload=False)
