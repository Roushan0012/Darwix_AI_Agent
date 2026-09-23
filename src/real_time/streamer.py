"""
Streaming Audio Pipeline & Nudge Orchestrator.
Processes real-time audio chunks or simulated live call stream, extracts signals,
filters nudges, and tracks P50/P95 latency.
"""

import time
import asyncio
from typing import List, Dict, Any, Callable, Optional

from src.real_time.signal_detector import SignalDetector
from src.real_time.nudge_controller import NudgeController
from src.real_time.latency_tracker import LatencyTracker

class RealTimePipeline:
    def __init__(
        self,
        signal_detector: Optional[SignalDetector] = None,
        nudge_controller: Optional[NudgeController] = None,
        latency_tracker: Optional[LatencyTracker] = None
    ):
        self.signal_detector = signal_detector or SignalDetector()
        self.nudge_controller = nudge_controller or NudgeController()
        self.latency_tracker = latency_tracker or LatencyTracker()
        self.transcript_history: List[Dict[str, str]] = []

    def process_chunk(
        self,
        speaker: str,
        text: Optional[str] = None,
        text_chunk: Optional[str] = None,
        simulated_asr_latency_ms: float = 240.0
    ) -> Dict[str, Any]:
        chunk_content = text or text_chunk or ""
        """
        Processes an incoming streaming audio speech chunk through the real-time pipeline.
        Measures exact component timings.
        """
        t_ingest = time.time()
        
        # Simulate / measure ASR transcription delay
        time.sleep(simulated_asr_latency_ms / 1000.0)
        t_asr_done = time.time()

        # Update rolling conversation window
        self.transcript_history.append({"speaker": speaker, "text": chunk_content})
        recent_window = "\n".join([f"{item['speaker'].upper()}: {item['text']}" for item in self.transcript_history[-4:]])

        # Step 2: Signal Extraction LLM
        raw_signal = self.signal_detector.detect_signal(recent_window)
        t_signal_done = time.time()

        # Step 3: Nudge Controller Filtering
        emitted_nudge = self.nudge_controller.evaluate_and_filter(raw_signal)
        
        # Step 4: Delivery timestamp
        t_delivered = time.time()

        chunk_id = f"chunk_{len(self.transcript_history)}"
        self.latency_tracker.record_stage(
            chunk_id=chunk_id,
            t_ingest=t_ingest,
            t_asr_done=t_asr_done,
            t_signal_done=t_signal_done,
            t_delivered=t_delivered
        )

        return {
            "chunk_id": chunk_id,
            "speaker": speaker,
            "text": chunk_content,
            "raw_signal": raw_signal,
            "nudge": emitted_nudge,
            "latency_ms": round((t_delivered - t_ingest) * 1000, 2)
        }
