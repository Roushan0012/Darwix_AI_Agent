"""
Nudge Controller Engine.
Applies precision controls: confidence filtering, duplicate suppression, cooldown windows,
priority queues, and auto-expiry to eliminate alert fatigue.
"""

import time
from typing import Dict, Any, Optional, List

class NudgeController:
    def __init__(
        self,
        min_confidence: float = 0.80,
        cooldown_seconds: float = 30.0,
        expiry_seconds: float = 20.0
    ):
        self.min_confidence = min_confidence
        self.cooldown_seconds = cooldown_seconds
        self.expiry_seconds = expiry_seconds
        
        # Track last trigger timestamps by signal type
        self.last_triggered: Dict[str, float] = {}
        
        # Active nudges list
        self.active_nudges: List[Dict[str, Any]] = []
        
        # False-positive / suppression analytics
        self.stats = {
            "total_signals_evaluated": 0,
            "nudges_emitted": 0,
            "suppressed_low_confidence": 0,
            "suppressed_cooldown": 0,
            "suppressed_none": 0
        }

    def evaluate_and_filter(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluates a raw signal against suppression rules.
        Returns a formatted Nudge object if approved, or None if suppressed.
        """
        self.stats["total_signals_evaluated"] += 1
        now = time.time()
        sig_type = signal.get("signal_type", "none")
        confidence = float(signal.get("confidence", 0.0))

        if sig_type == "none":
            self.stats["suppressed_none"] += 1
            return None

        # Rule 1: Confidence Threshold Filter
        if confidence < self.min_confidence:
            self.stats["suppressed_low_confidence"] += 1
            return None

        # Rule 2: Cooldown & Duplicate Suppression Filter
        last_time = self.last_triggered.get(sig_type, 0.0)
        if (now - last_time) < self.cooldown_seconds:
            self.stats["suppressed_cooldown"] += 1
            return None

        # Approved: Register trigger time
        self.last_triggered[sig_type] = now
        self.stats["nudges_emitted"] += 1

        nudge = {
            "nudge_id": f"nudge_{int(now * 1000)}",
            "signal_type": sig_type,
            "priority": signal.get("priority", "MEDIUM"),
            "confidence": confidence,
            "nudge_text": signal.get("nudge_text", ""),
            "evidence": signal.get("evidence", ""),
            "emitted_at": now,
            "expires_at": now + self.expiry_seconds
        }
        self.active_nudges.append(nudge)
        return nudge

    def prune_expired(self) -> List[Dict[str, Any]]:
        """Removes expired nudges based on time-to-live."""
        now = time.time()
        self.active_nudges = [n for n in self.active_nudges if n["expires_at"] > now]
        return self.active_nudges

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Provides empirical precision and false-positive suppression breakdown."""
        total = self.stats["total_signals_evaluated"]
        emitted = self.stats["nudges_emitted"]
        suppressed = total - emitted

        return {
            "total_signals_evaluated": total,
            "nudges_emitted": emitted,
            "total_suppressed": suppressed,
            "suppression_rate_pct": round((suppressed / total * 100), 2) if total > 0 else 0.0,
            "suppression_breakdown": {
                "low_confidence_suppressed": self.stats["suppressed_low_confidence"],
                "cooldown_suppressed": self.stats["suppressed_cooldown"],
                "no_signal_suppressed": self.stats["suppressed_none"]
            }
        }
