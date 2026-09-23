"""
Real-Time Signal Detection Engine.
Extracts compliance risks, missed cross-sells, customer sentiment/frustration, and payment difficulties.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SIGNAL_EXTRACTION_PROMPT = """You are a Real-Time Banking & Lending Compliance & Sales Intelligence Monitor.
Analyze the ongoing dialogue between the AGENT and CUSTOMER.

Detect if any of the following 4 critical signals are present:
1. `missed_cross_sell`: Customer mentions having additional assets, secondary vehicles, fleet expansion, equipment needs, or inventory spikes that could benefit from another product (e.g. equipment leasing, invoice factoring).
2. `compliance_gap`: Agent quotes interest rate or loan amounts WITHOUT stating the mandatory 3.0% origination fee, APR disclosure, or asks for collateral on an unsecured loan.
3. `rising_frustration`: Customer expresses irritation, repeated questions, confusion, or dissatisfaction with paperwork or delays.
4. `payment_difficulty`: Customer mentions seasonal cash crunch, delayed invoice receivables, or difficulty meeting fixed monthly due dates.

RULES:
- Return ONLY valid JSON with no markdown wrapping.
- If audio is ambiguous, incomplete greeting, casual chit-chat, or noisy with no clear trigger, set `signal_type` to "none" and `confidence` < 0.5.
- Be precise. Avoid false positives.

JSON Schema:
{
  "signal_type": "missed_cross_sell" | "compliance_gap" | "rising_frustration" | "payment_difficulty" | "none",
  "confidence": 0.0 to 1.0,
  "evidence": "Exact snippet from dialogue justifying this trigger",
  "nudge_text": "Short actionable instruction for the agent (e.g. 'Remind customer of mandatory 3% origination fee before proceeding')",
  "priority": "HIGH" | "MEDIUM" | "LOW"
}
"""

class SignalDetector:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.api_key)
        self.model = "qwen/qwen3.8-27b"

    def detect_signal(self, recent_dialogue: str) -> Dict[str, Any]:
        """
        Analyzes recent conversation slice and returns structured signal detection JSON.
        """
        t0 = time.time()
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SIGNAL_EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Recent Dialogue:\n{recent_dialogue}"}
                ],
                temperature=0.1,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            parsed["inference_time_ms"] = round((time.time() - t0) * 1000, 2)
            return parsed
        except Exception as e:
            return {
                "signal_type": "none",
                "confidence": 0.0,
                "evidence": f"Error: {str(e)}",
                "nudge_text": "",
                "priority": "LOW",
                "inference_time_ms": round((time.time() - t0) * 1000, 2)
            }
