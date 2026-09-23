"""
Document Parser and Knowledge Ingestion Pipeline.
Extracts, chunks, and structures raw heterogeneous business documents (Markdown, Tables, HTML).
"""

import os
import json
import re
from typing import List
from pathlib import Path

from src.kb.schema import KBRecord
from src.kb.cleaner import Cleaner

class DocumentParser:
    def __init__(self, raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed"):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.cleaner = Cleaner()

    def parse_markdown(self, filepath: Path) -> List[KBRecord]:
        """Parses markdown files into section-based chunks with header tracking."""
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by top-level or second-level headers
        sections = re.split(r'\n(?=#{1,2}\s+)', content)
        doc_name = filepath.name

        for idx, section in enumerate(sections):
            cleaned_text, is_dup, had_pii = self.cleaner.clean_chunk(section)
            if not cleaned_text or is_dup:
                continue

            # Extract title from first line
            first_line = cleaned_text.split('\n')[0].strip('# ').strip()
            title = first_line if first_line else f"{doc_name} Section {idx+1}"

            # Determine category
            category = "general_policy"
            if "qualification" in title.lower() or "eligibility" in title.lower():
                category = "qualification_rules"
            elif "objection" in title.lower() or "faq" in title.lower():
                category = "objections_and_faqs"
            elif "repayment" in title.lower() or "pricing" in title.lower():
                category = "product_terms"

            record_id = f"kb_{filepath.stem[:6]}_{idx+1:03d}"
            record = KBRecord(
                record_id=record_id,
                title=title,
                content=cleaned_text,
                category=category,
                source=f"{doc_name}#section_{idx+1}",
                version="2.1",
                pii=False,  # PII is verified scrubbed
                metadata={"source_file": doc_name, "raw_had_pii": had_pii}
            )
            records.append(record)

        return records

    def parse_json_table(self, filepath: Path) -> List[KBRecord]:
        """Parses structured JSON tables into searchable product records."""
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data):
            p_id = item.get("product_id", f"PROD_{idx+1}")
            p_name = item.get("product_name", "Loan Product")
            
            # Formulate structured text chunk
            content_lines = [
                f"Product: {p_name} ({p_id})",
                f"Target Segment: {item.get('target_segment', 'N/A')}",
                f"Facility Amount Range: ${item.get('min_amount', 0):,} to ${item.get('max_amount', 0):,}",
                f"Tenor Duration: {item.get('min_tenor_months', 0)} to {item.get('max_tenor_months', 0)} months",
                f"Nominal Interest Rate: {item.get('monthly_interest_rate', 'N/A')}",
                f"Origination Processing Fee: {item.get('origination_fee_pct', 0)}%",
                f"Collateral Required: {'Yes' if item.get('collateral_required') else 'No (Unsecured)'}",
                f"Personal Guarantee Required: {'Yes' if item.get('personal_guarantee_required') else 'No'}",
                f"Funding Speed: {item.get('disbursement_speed', 'Standard')}"
            ]
            content_text = "\n".join(content_lines)
            cleaned_text, is_dup, had_pii = self.cleaner.clean_chunk(content_text)

            record = KBRecord(
                record_id=f"kb_table_{p_id.lower()}",
                title=f"{p_name} Terms & Parameters",
                content=cleaned_text,
                category="product_terms",
                source=f"{filepath.name}#{p_id}",
                version="1.0",
                pii=False,
                metadata=item
            )
            records.append(record)

        return records

    def parse_html(self, filepath: Path) -> List[KBRecord]:
        """Extracts article content from HTML, strips navigation/footers, and scrubs inquiry PII."""
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        # Extract main article content
        article_match = re.search(r'<article>(.*?)</article>', html, flags=re.DOTALL)
        if article_match:
            article_raw = re.sub(r'<[^>]+>', ' ', article_match.group(1))
            cleaned_text, is_dup, had_pii = self.cleaner.clean_chunk(article_raw)
            if cleaned_text and not is_dup:
                records.append(KBRecord(
                    record_id="kb_product_001",
                    title="Branch Partnership Benefits",
                    content=cleaned_text,
                    category="partnership_benefits",
                    source=f"{filepath.name}#article",
                    version="1.0",
                    pii=False,
                    metadata={"had_pii": had_pii}
                ))

        # Extract pilot inquiries section with PII scrubbing demonstration
        inquiries_match = re.search(r'<section id="sample-submissions">(.*?)</section>', html, flags=re.DOTALL)
        if inquiries_match:
            inquiry_raw = re.sub(r'<[^>]+>', ' ', inquiries_match.group(1))
            cleaned_text, is_dup, had_pii = self.cleaner.clean_chunk(inquiry_raw)
            if cleaned_text and not is_dup:
                records.append(KBRecord(
                    record_id="kb_pilot_inquiries_002",
                    title="Pilot Inquiry Records (Sanitized)",
                    content=cleaned_text,
                    category="customer_samples",
                    source=f"{filepath.name}#sample-submissions",
                    version="1.0",
                    pii=False,
                    metadata={"had_pii": had_pii, "pii_redacted": True}
                ))

        return records

    def ingest_all(self) -> List[KBRecord]:
        """Ingests and standardizes all raw documents in the raw data directory."""
        all_records = []

        for file in self.raw_data_dir.iterdir():
            if file.suffix in [".md", ".markdown"]:
                all_records.extend(self.parse_markdown(file))
            elif file.suffix == ".json":
                all_records.extend(self.parse_json_table(file))
            elif file.suffix in [".html", ".htm"]:
                all_records.extend(self.parse_html(file))

        # Persist the processed knowledge base to disk
        out_file = self.processed_data_dir / "knowledge_base.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in all_records], f, indent=2)

        print(f"Successfully ingested and cleaned {len(all_records)} traceable KB records into {out_file}")
        return all_records

if __name__ == "__main__":
    parser = DocumentParser()
    parser.ingest_all()
