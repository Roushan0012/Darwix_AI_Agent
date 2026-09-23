"""
Voice Agent Test Suite for Question 1.
Executes and records the 3 mandatory test call flows:
1. Cooperative Customer (qualification & mock CRM lead creation)
2. Grounded Objection Handling (dynamic RAG tool calling)
3. Incomplete Details, Out-of-Scope Fallback & Human Escalation
Generates full audio files (.mp3) and structured transcript markdown logs.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.voice.agent import VoiceAgent
from src.voice.audio_service import AudioService
from src.kb.store import KnowledgeStore

load_dotenv()

TEST_CALL_SCENARIOS = [
    {
        "call_id": "CALL_01_COOPERATIVE",
        "title": "Cooperative Customer - Smooth Qualification & CRM Lead Creation",
        "turns": [
            "Hello, I am calling to apply for an unsecured business loan for my business, Apex Logistics.",
            "We have been operating for 28 consecutive months, and our verified average monthly revenue is $35,000. I am looking for a $50,000 working capital loan.",
            "My personal credit score is 690 with no bankruptcies or defaults."
        ]
    },
    {
        "call_id": "CALL_02_OBJECTION",
        "title": "Grounded Objection Handling & Product Policy Queries",
        "turns": [
            "Hi, I noticed your interest rates are between 1.25% and 2.1% a month. Why is your interest rate higher than traditional tier-1 commercial banks?",
            "Do I have to pledge my personal house or real estate property as collateral for this working capital loan?",
            "What happens if I decide to repay the entire loan balance early after 7 months?"
        ]
    },
    {
        "call_id": "CALL_03_FALLBACK_ESCALATION",
        "title": "Incomplete/Conflicting Details, Out-of-Scope Fallback & Human Escalation",
        "turns": [
            "Hi, I need fast funding, but my business has only been open for 3 months and revenue is under $5,000.",
            "Do you guys also provide student debt consolidation or personal auto loans for teenagers?",
            "I need special approval. Please transfer me to a human loan officer or supervisor right now."
        ]
    }
]

def run_test_calls():
    print("="*80)
    print("RUNNING QUESTION 1 VOICE AGENT CALL RECORDING & TEST COVERAGE")
    print("="*80)

    kb_store = KnowledgeStore.load_from_processed("data/processed/knowledge_base.json")
    agent = VoiceAgent(kb_store=kb_store)
    audio_service = AudioService(output_dir="recordings")

    transcripts_dir = Path("transcripts")
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# Question 1: Voice Agent Test Calls & Verification Transcripts",
        "",
        "This document contains the verified dialogue transcripts, RAG tool invocations, safe fallback responses, and CRM actions for Question 1.",
        ""
    ]

    for scenario in TEST_CALL_SCENARIOS:
        c_id = scenario["call_id"]
        print(f"\n--- EXECUTING {c_id}: {scenario['title']} ---")
        session_id = f"test_{c_id.lower()}"
        dialogue_log = []
        call_audio_chunks = []

        report_lines.extend([
            f"## {scenario['title']} (`{c_id}`)",
            f"- **Audio Recording**: [`recordings/{c_id.lower()}.mp3`](../recordings/{c_id.lower()}.mp3)",
            ""
        ])

        for idx, user_turn in enumerate(scenario["turns"]):
            print(f"\n[Turn {idx+1}] Caller: \"{user_turn}\"")
            turn_res = agent.process_turn(user_text=user_turn, session_id=session_id)
            bot_text = turn_res["bot_response"]
            print(f"[Turn {idx+1}] Agent : \"{bot_text}\"")

            citations = turn_res["citations_used"]
            if citations:
                print(f"  |-- [RAG Citations]: {citations}")

            report_lines.extend([
                f"**Caller (Turn {idx+1})**: *\"{user_turn}\"*",
                f"**Agent**: {bot_text}",
            ])
            if citations:
                for c in citations:
                    report_lines.append(f"> 🔍 **KB Grounded Citation**: `{c}`")
            report_lines.append("")

            dialogue_log.append(f"Caller: {user_turn}\nAgent: {bot_text}")

        # Synthesize combined call audio demonstration
        full_call_script = " ... Next turn ... ".join(dialogue_log)
        audio_filename = f"{c_id.lower()}.mp3"
        audio_path = audio_service.synthesize_speech(
            text=full_call_script,
            output_filename=audio_filename,
            language="en"
        )
        print(f"  |-- [AUDIO] Audio synthesized to: {audio_path}")

        # Summary of call state
        final_state = agent.sessions[session_id]
        status = final_state["status"]
        escalated = final_state["escalated"]
        report_lines.extend([
            f"**Final Call Status**: `{status}` | **Escalated**: `{escalated}`",
            "---",
            ""
        ])

    transcript_file = transcripts_dir / "call_transcripts.md"
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nSaved all transcripts and verification evidence to {transcript_file}")

if __name__ == "__main__":
    run_test_calls()
