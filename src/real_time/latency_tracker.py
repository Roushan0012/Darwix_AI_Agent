"""
Real-Time Latency Tracker for Streaming Audio & Nudge Pipeline.
Measures chunk-level timestamps and calculates P50 and P95 latency across pipeline stages:
Audio Chunk Ingestion -> ASR -> Signal Extraction -> Nudge Delivery.
"""

import time
import numpy as np
from typing import Dict, List, Any

class LatencyTracker:
    def __init__(self):
        self.records: List[Dict[str, float]] = []

    def record_stage(
        self,
        chunk_id: str,
        t_ingest: float,
        t_asr_done: float,
        t_signal_done: float,
        t_delivered: float
    ):
        asr_latency = (t_asr_done - t_ingest) * 1000
        signal_latency = (t_signal_done - t_asr_done) * 1000
        delivery_latency = (t_delivered - t_signal_done) * 1000
        e2e_latency = (t_delivered - t_ingest) * 1000

        self.records.append({
            "chunk_id": chunk_id,
            "asr_latency_ms": round(asr_latency, 2),
            "signal_latency_ms": round(signal_latency, 2),
            "delivery_latency_ms": round(delivery_latency, 2),
            "e2e_latency_ms": round(e2e_latency, 2)
        })

    def get_summary(self) -> Dict[str, Any]:
        if not self.records:
            return {"error": "No latency records recorded yet"}

        e2e = [r["e2e_latency_ms"] for r in self.records]
        asr = [r["asr_latency_ms"] for r in self.records]
        signal = [r["signal_latency_ms"] for r in self.records]
        delivery = [r["delivery_latency_ms"] for r in self.records]

        return {
            "total_chunks_processed": len(self.records),
            "end_to_end": {
                "p50_ms": round(float(np.percentile(e2e, 50)), 2),
                "p95_ms": round(float(np.percentile(e2e, 95)), 2),
                "mean_ms": round(float(np.mean(e2e)), 2),
                "min_ms": round(float(np.min(e2e)), 2),
                "max_ms": round(float(np.max(e2e)), 2),
            },
            "component_breakdown_p50_ms": {
                "asr_transcription": round(float(np.percentile(asr, 50)), 2),
                "signal_extraction_llm": round(float(np.percentile(signal, 50)), 2),
                "delivery_websocket": round(float(np.percentile(delivery, 50)), 2)
            },
            "component_breakdown_p95_ms": {
                "asr_transcription": round(float(np.percentile(asr, 95)), 2),
                "signal_extraction_llm": round(float(np.percentile(signal, 95)), 2),
                "delivery_websocket": round(float(np.percentile(delivery, 95)), 2)
            }
        }
