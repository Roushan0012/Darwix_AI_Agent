"""
Data Cleaning and PII Protection Engine.
Removes navigation artifacts, scrubs PII, eliminates duplicate & near-duplicate content, and normalizes terminology.
"""

import re
import hashlib
from typing import Tuple, List, Set, Dict

# Regex patterns for Personally Identifiable Information (PII)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
SSN_TAXID_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{2}-\d{7}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
APPLICANT_NAME_PATTERN = re.compile(r'(Applicant:\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)')

class Cleaner:
    """Handles text cleaning, PII redaction, deduplication, and terminology standardization."""

    def __init__(self):
        self.seen_word_sets: List[Set[str]] = []

    def scrub_pii(self, text: str) -> Tuple[str, bool]:
        """
        Detects and masks PII with compliant placeholder tokens.
        Returns:
            (sanitized_text, had_pii_flag)
        """
        had_pii = False

        if EMAIL_PATTERN.search(text):
            text = EMAIL_PATTERN.sub('[REDACTED_EMAIL]', text)
            had_pii = True

        if SSN_TAXID_PATTERN.search(text):
            text = SSN_TAXID_PATTERN.sub('[REDACTED_TAX_ID]', text)
            had_pii = True

        if CREDIT_CARD_PATTERN.search(text):
            text = CREDIT_CARD_PATTERN.sub('[REDACTED_CARD_NUMBER]', text)
            had_pii = True

        if PHONE_PATTERN.search(text):
            text = PHONE_PATTERN.sub('[REDACTED_PHONE]', text)
            had_pii = True

        if APPLICANT_NAME_PATTERN.search(text):
            text = APPLICANT_NAME_PATTERN.sub(r'\1[REDACTED_NAME]', text)
            had_pii = True

        return text, had_pii

    def normalize_text(self, text: str) -> str:
        """Standardizes terminology, spaces, and formatting without double-replacements."""
        # Normalize multiple spaces and newlines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text).strip()

        # Fix "Nominal Nominal" if it occurred
        text = re.sub(r'\b(Nominal\s+)+Nominal\b', 'Nominal', text, flags=re.IGNORECASE)
        # Standardize "interest rate" if not already prefixed with Nominal
        text = re.sub(r'(?<!Nominal\s)\binterest rate\b', 'Nominal Interest Rate', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpre-payment\b', 'Prepayment', text, flags=re.IGNORECASE)
        text = re.sub(r'\bturn-around time\b', 'Turnaround Time', text, flags=re.IGNORECASE)
        text = re.sub(r'\bapr\b', 'APR', text, flags=re.IGNORECASE)
        text = re.sub(r'\bach\b', 'ACH', text, flags=re.IGNORECASE)

        return text

    def is_near_duplicate_or_subset(self, text: str, containment_threshold: float = 0.78) -> bool:
        """
        Detects exact, near-duplicate, or redundant subset sections using Szymkiewicz–Simpson overlap coefficient.
        """
        words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        stop_words = {'the', 'and', 'for', 'must', 'with', 'have', 'been', 'this', 'that', 'from', 'section'}
        content_words = words - stop_words

        if len(content_words) < 6:
            return False

        for seen in self.seen_word_sets:
            intersection = len(content_words & seen)
            min_len = min(len(content_words), len(seen))
            if min_len > 0 and (intersection / min_len) >= containment_threshold:
                return True

        self.seen_word_sets.append(content_words)
        return False

    def clean_chunk(self, raw_text: str) -> Tuple[str, bool, bool]:
        """
        Full cleaning pipeline for a chunk.
        Returns:
            (cleaned_text, is_duplicate, had_pii)
        """
        # Step 1: Remove navigation artifacts, comments, and boilerplate footers
        cleaned = re.sub(r'<!--.*?-->', '', raw_text, flags=re.DOTALL)
        cleaned = re.sub(r'\[Home\].*?\[Apply Now\]', '', cleaned)
        cleaned = re.sub(r'-{5,}', '', cleaned)
        cleaned = re.sub(r'Confidential - For Internal and Authorized Partner Use Only.*', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'Cookie settings.*?Information', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # Discard header-only or trivial empty chunks (< 10 non-header words)
        words_count = len(re.findall(r'\w+', re.sub(r'#+\s*.*', '', cleaned)))
        if words_count < 8 and len(cleaned.split('\n')) <= 2:
            return "", False, False

        if not cleaned:
            return "", False, False

        # Step 2: Check near-duplication / subset containment
        if self.is_near_duplicate_or_subset(cleaned):
            return "", True, False

        # Step 3: Scrub PII
        sanitized, had_pii = self.scrub_pii(cleaned)

        # Step 4: Normalize terminology
        normalized = self.normalize_text(sanitized)

        return normalized, False, had_pii
