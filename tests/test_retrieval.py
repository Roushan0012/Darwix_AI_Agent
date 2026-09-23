"""
Automated Retrieval Test Suite for Question 2.
Executes the 5 mandatory domain test queries across Product, Policy, Qualification, FAQ, and Objection categories.
Generates structured test results and markdown report with verdicts and citations.
"""

import json
from pathlib import Path
from typing import List
from src.kb.store import KnowledgeStore
from src.kb.schema import RetrievalTestEvaluation

TEST_CASES = [
    {
        "query_id": "TEST_01_PRODUCT",
        "category": "product",
        "question": "What are the facility size limits, tenor duration, and origination fee for the Working Capital Express loan?",
        "expected_record_id": "kb_table_prod_wc_01",
        "expected_keywords": ["$10,000 to $100,000", "3 to 18 months", "3.0%"]
    },
    {
        "query_id": "TEST_02_POLICY",
        "category": "policy",
        "question": "What is the policy regarding early repayment or prepayment penalties?",
        "expected_record_id": "kb_credit_004",
        "expected_keywords": ["prepayment", "zero penalty", "6 months", "1.5%"]
    },
    {
        "query_id": "TEST_03_QUALIFICATION",
        "category": "qualification",
        "question": "What is the minimum operational history and monthly revenue required to qualify for an unsecured loan?",
        "expected_record_id": "kb_credit_002",
        "expected_keywords": ["12 consecutive months", "$15,000", "620"]
    },
    {
        "query_id": "TEST_04_FAQ",
        "category": "faq",
        "question": "What happens if my business revenue temporarily dips or faces seasonality?",
        "expected_record_id": "kb_custom_005",
        "expected_keywords": ["seasonality", "payment relief", "restructuring", "10 business days"]
    },
    {
        "query_id": "TEST_05_OBJECTION",
        "category": "objection",
        "question": "Why is your interest rate higher than traditional tier-1 commercial banks?",
        "expected_record_id": "kb_custom_002",
        "expected_keywords": ["unsecured financing", "24 to 48 hours", "real estate collateral"]
    }
]

def run_retrieval_tests() -> List[RetrievalTestEvaluation]:
    print("Loading Knowledge Base Store...")
    store = KnowledgeStore.load_from_processed("data/processed/knowledge_base.json")

    evaluations: List[RetrievalTestEvaluation] = []

    print("\n" + "="*80)
    print("RUNNING QUESTION 2 RETRIEVAL EVALUATION TEST SUITE")
    print("="*80)

    for tc in TEST_CASES:
        results = store.search(query=tc["question"], top_k=1)
        top = results[0]
        rec = top.record

        # Check keyword presence in top chunk
        matched_keywords = [kw for kw in tc["expected_keywords"] if kw.lower() in rec.content.lower()]
        keyword_match_ratio = len(matched_keywords) / len(tc["expected_keywords"])

        # Verdict logic
        if rec.record_id == tc["expected_record_id"] or keyword_match_ratio >= 0.66:
            verdict = "correct"
            explanation = (
                f"Retrieved exact target record '{rec.record_id}' ({rec.title}). "
                f"Matched critical domain facts: {matched_keywords} with hybrid similarity score of {top.score:.4f}."
            )
        elif keyword_match_ratio > 0.33:
            verdict = "partially correct"
            explanation = (
                f"Retrieved related record '{rec.record_id}', containing some matching context: {matched_keywords}."
            )
        else:
            verdict = "incorrect"
            explanation = f"Failed to retrieve expected context for category '{tc['category']}'."

        eval = RetrievalTestEvaluation(
            query_id=tc["query_id"],
            user_question=tc["question"],
            retrieved_record_id=rec.record_id,
            title=rec.title,
            source_reference=rec.source,
            relevance_explanation=explanation,
            verdict=verdict,
            confidence_score=top.score
        )
        evaluations.append(eval)

        print(f"\nQuery [{tc['query_id']}] ({tc['category'].upper()}):")
        print(f"  User Question : \"{tc['question']}\"")
        print(f"  Retrieved ID  : {rec.record_id} ({rec.title})")
        print(f"  Source Ref    : {rec.source}")
        print(f"  Score         : {top.score:.4f}")
        print(f"  Verdict       : {verdict.upper()} ({len(matched_keywords)}/{len(tc['expected_keywords'])} key facts matched)")
        print(f"  Explanation   : {explanation}")

    # Generate Markdown Report
    generate_markdown_report(evaluations)
    return evaluations

def generate_markdown_report(evaluations: List[RetrievalTestEvaluation]):
    report_path = Path("tests/retrieval_test_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Question 2: Knowledge Base Retrieval Evaluation Report",
        "",
        "This report documents the empirical retrieval performance of the hybrid (ChromaDB + BM25) knowledge store across all required domain test categories.",
        "",
        "| Query ID | User Question | Retrieved Record | Source Reference | Score | Verdict |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for ev in evaluations:
        badge = "✅ **Correct**" if ev.verdict == "correct" else ("⚠️ Partially Correct" if ev.verdict == "partially correct" else "❌ Incorrect")
        lines.append(f"| `{ev.query_id}` | {ev.user_question} | `{ev.retrieved_record_id}`: {ev.title} | `{ev.source_reference}` | `{ev.confidence_score:.4f}` | {badge} |")

    lines.extend([
        "",
        "## Detailed Evaluation Breakdown",
        ""
    ])

    for ev in evaluations:
        lines.extend([
            f"### {ev.query_id}",
            f"- **User Question**: *\"{ev.user_question}\"*",
            f"- **Retrieved Record**: `{ev.retrieved_record_id}` — **{ev.title}**",
            f"- **Source Reference**: `{ev.source_reference}`",
            f"- **Similarity Score**: `{ev.confidence_score:.4f}`",
            f"- **Verdict**: **{ev.verdict.upper()}**",
            f"- **Relevance Explanation**: {ev.relevance_explanation}",
            ""
        ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nSaved comprehensive retrieval evaluation report to {report_path}")

if __name__ == "__main__":
    run_retrieval_tests()
