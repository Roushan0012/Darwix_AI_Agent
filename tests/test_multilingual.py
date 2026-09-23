"""
Multilingual Voice Bots Test Suite for Question 3.
Executes 2 calls for Philippines (Taglish Bancassurance) and 2 calls for Indonesia (Bahasa Multifinance).
Generates native speech audio files and structured markdown transcripts.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.multilingual.philippines_bot import PhilippinesVoiceBot
from src.multilingual.indonesia_bot import IndonesiaVoiceBot
from src.voice.audio_service import AudioService

load_dotenv()

PH_SCENARIOS = [
    {
        "call_id": "PH_CALL_01_RENEWAL",
        "title": "Philippines Bancassurance - Policy Renewal & Premium Payment Reminder",
        "turns": [
            "Hello po, nakatanggap po ako ng SMS regarding my policy renewal sa Darwix Life.",
            "Magkano po ba ang annual premium ko, at pwede po ba itong i-auto debit na lang sa BDO account ko?",
            "Sige po ma'am, paki-enroll na lang po sa auto-debit para hindi mag-lapse ang coverage ko."
        ]
    },
    {
        "call_id": "PH_CALL_02_OBJECTION",
        "title": "Philippines Bancassurance - Premium Objection & Human Escalation",
        "turns": [
            "Hi po, medyo masikip po ang budget ko ngayon, balak ko sanang i-cancel o ihinto muna ang monthly premium ko.",
            "May ibang options po ba ako bukod sa cancellation para hindi masayang yung naihulog ko?",
            "Gusto ko pong makausap ang branch relationship manager ko para ma-explain nang maayos. Pwede po bang paki-transfer?"
        ]
    }
]

ID_SCENARIOS = [
    {
        "call_id": "ID_CALL_01_INSTALLMENT",
        "title": "Indonesia Multifinance - Installment Reminder & Payment Confirmation",
        "turns": [
            "Halo selamat siang, saya mau tanya soal jadwal jatuh tempo cicilan mobil saya bulan ini.",
            "Kira-kira berapa jumlah angsuran yang harus saya bayar dan apakah ada denda keterlambatan kalau saya bayar tanggal 27?",
            "Baik Pak, saya akan bayar via transfer Virtual Account BCA sebelum tanggal 25 ya."
        ]
    },
    {
        "call_id": "ID_CALL_02_RESTRUCTURING",
        "title": "Indonesia Multifinance - Tenor Restructuring & Colloquial Javanese Nuance",
        "turns": [
            "Halo Mas Budi, ini dengan Pak Joko. Waduh, usaha bengkel saya lagi sepi nih mas, angsurannya agak berat bulan ini.",
            "Bisa ndak ya mas kalau tenor pembiayaannya diperpanjang dari 24 bulan jadi 36 bulan biar cicilan per bulannya lebih enteng?",
            "Nggih mas, tolong sambungkan ke petugas kredit yang berwenang ya mas untuk urus restrukturisasinya."
        ]
    }
]

def run_multilingual_tests():
    print("="*80)
    print("RUNNING QUESTION 3 MULTILINGUAL VOICE BOTS TEST SUITE")
    print("="*80)

    audio_service = AudioService(output_dir="recordings")
    transcripts_dir = Path("transcripts")
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Question 3: Multilingual Voice Bots Test Transcripts",
        "",
        "This document contains the verified conversation transcripts and audio evidence for localized financial voice bots in the **Philippines** (Taglish Bancassurance) and **Indonesia** (Bahasa Multifinance).",
        ""
    ]

    # 1. Run Philippines Bot
    print("\n--- [PHILIPPINES BANCASSURANCE BOT] ---")
    for sc in PH_SCENARIOS:
        c_id = sc["call_id"]
        print(f"\nExecuting {c_id}: {sc['title']}")
        bot = PhilippinesVoiceBot()
        dialogue_log = []

        report_lines.extend([
            f"## {sc['title']} (`{c_id}`)",
            f"- **Market**: Philippines (Bancassurance / Life Insurance)",
            f"- **Language Register**: Natural Taglish (Filipino + English code-switching with *po/opo*)",
            f"- **Audio File**: [`recordings/{c_id.lower()}.mp3`](../recordings/{c_id.lower()}.mp3)",
            ""
        ])

        for idx, u_turn in enumerate(sc["turns"]):
            print(f"  [Turn {idx+1}] Caller: \"{u_turn}\"")
            b_turn = bot.process_turn(u_turn)
            print(f"  [Turn {idx+1}] Agent : \"{b_turn}\"")

            report_lines.extend([
                f"**Customer (Turn {idx+1})**: *\"{u_turn}\"*",
                f"**Agent (Taglish)**: {b_turn}",
                ""
            ])
            dialogue_log.append(f"Customer: {u_turn}\nAgent: {b_turn}")

        # Synthesize audio with Filipino neural voice
        audio_filename = f"{c_id.lower()}.mp3"
        audio_path = audio_service.synthesize_speech(
            text=" ... Kasunod na linya ... ".join(dialogue_log),
            output_filename=audio_filename,
            language="fil"
        )
        print(f"  |-- [AUDIO] Generated Filipino voice: {audio_path}")
        report_lines.append("---\n")

    # 2. Run Indonesia Bot
    print("\n--- [INDONESIA MULTIFINANCE BOT] ---")
    for sc in ID_SCENARIOS:
        c_id = sc["call_id"]
        print(f"\nExecuting {c_id}: {sc['title']}")
        bot = IndonesiaVoiceBot()
        dialogue_log = []

        report_lines.extend([
            f"## {sc['title']} (`{c_id}`)",
            f"- **Market**: Indonesia (Consumer Multifinance & Credit)",
            f"- **Language Register**: Bahasa Indonesia (Formal-Colloquial with Regional Loanwords)",
            f"- **Audio File**: [`recordings/{c_id.lower()}.mp3`](../recordings/{c_id.lower()}.mp3)",
            ""
        ])

        for idx, u_turn in enumerate(sc["turns"]):
            print(f"  [Turn {idx+1}] Caller: \"{u_turn}\"")
            b_turn = bot.process_turn(u_turn)
            print(f"  [Turn {idx+1}] Agent : \"{b_turn}\"")

            report_lines.extend([
                f"**Nasabah (Turn {idx+1})**: *\"{u_turn}\"*",
                f"**Agent (Bahasa)**: {b_turn}",
                ""
            ])
            dialogue_log.append(f"Nasabah: {u_turn}\nAgent: {b_turn}")

        # Synthesize audio with Indonesian neural voice
        audio_filename = f"{c_id.lower()}.mp3"
        audio_path = audio_service.synthesize_speech(
            text=" ... Giliran berikutnya ... ".join(dialogue_log),
            output_filename=audio_filename,
            language="id"
        )
        print(f"  |-- [AUDIO] Generated Indonesian voice: {audio_path}")
        report_lines.append("---\n")

    transcript_file = transcripts_dir / "multilingual_transcripts.md"
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nSaved all multilingual transcripts to {transcript_file}")

if __name__ == "__main__":
    run_multilingual_tests()
