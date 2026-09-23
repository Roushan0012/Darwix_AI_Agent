# Question 2: Knowledge Base Retrieval Evaluation Report

This report documents the empirical retrieval performance of the hybrid (ChromaDB + BM25) knowledge store across all required domain test categories.

| Query ID | User Question | Retrieved Record | Source Reference | Score | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TEST_01_PRODUCT` | What are the facility size limits, tenor duration, and origination fee for the Working Capital Express loan? | `kb_table_prod_wc_01`: Working Capital Express Terms & Parameters | `loan_products_table.json#PROD_WC_01` | `0.8509` | ✅ **Correct** |
| `TEST_02_POLICY` | What is the policy regarding early repayment or prepayment penalties? | `kb_credit_004`: Section 3: Early Repayment & Pre-termination Policy | `credit_policy_v2.md#section_4` | `0.9560` | ✅ **Correct** |
| `TEST_03_QUALIFICATION` | What is the minimum operational history and monthly revenue required to qualify for an unsecured loan? | `kb_credit_002`: Section 1: Minimum Borrower Qualification Criteria | `credit_policy_v2.md#section_2` | `0.9191` | ✅ **Correct** |
| `TEST_04_FAQ` | What happens if my business revenue temporarily dips or faces seasonality? | `kb_custom_005`: FAQ 4: "What happens if my business revenue temporarily dips?" | `customer_objections_faq.md#section_5` | `0.9290` | ✅ **Correct** |
| `TEST_05_OBJECTION` | Why is your interest rate higher than traditional tier-1 commercial banks? | `kb_custom_002`: Objection 1: "Why is your Nominal Interest Rate higher than traditional tier-1 commercial banks?" | `customer_objections_faq.md#section_2` | `0.9122` | ✅ **Correct** |

## Detailed Evaluation Breakdown

### TEST_01_PRODUCT
- **User Question**: *"What are the facility size limits, tenor duration, and origination fee for the Working Capital Express loan?"*
- **Retrieved Record**: `kb_table_prod_wc_01` — **Working Capital Express Terms & Parameters**
- **Source Reference**: `loan_products_table.json#PROD_WC_01`
- **Similarity Score**: `0.8509`
- **Verdict**: **CORRECT**
- **Relevance Explanation**: Retrieved exact target record 'kb_table_prod_wc_01' (Working Capital Express Terms & Parameters). Matched critical domain facts: ['$10,000 to $100,000', '3 to 18 months', '3.0%'] with hybrid similarity score of 0.8509.

### TEST_02_POLICY
- **User Question**: *"What is the policy regarding early repayment or prepayment penalties?"*
- **Retrieved Record**: `kb_credit_004` — **Section 3: Early Repayment & Pre-termination Policy**
- **Source Reference**: `credit_policy_v2.md#section_4`
- **Similarity Score**: `0.9560`
- **Verdict**: **CORRECT**
- **Relevance Explanation**: Retrieved exact target record 'kb_credit_004' (Section 3: Early Repayment & Pre-termination Policy). Matched critical domain facts: ['prepayment', 'zero penalty', '6 months', '1.5%'] with hybrid similarity score of 0.9560.

### TEST_03_QUALIFICATION
- **User Question**: *"What is the minimum operational history and monthly revenue required to qualify for an unsecured loan?"*
- **Retrieved Record**: `kb_credit_002` — **Section 1: Minimum Borrower Qualification Criteria**
- **Source Reference**: `credit_policy_v2.md#section_2`
- **Similarity Score**: `0.9191`
- **Verdict**: **CORRECT**
- **Relevance Explanation**: Retrieved exact target record 'kb_credit_002' (Section 1: Minimum Borrower Qualification Criteria). Matched critical domain facts: ['12 consecutive months', '$15,000', '620'] with hybrid similarity score of 0.9191.

### TEST_04_FAQ
- **User Question**: *"What happens if my business revenue temporarily dips or faces seasonality?"*
- **Retrieved Record**: `kb_custom_005` — **FAQ 4: "What happens if my business revenue temporarily dips?"**
- **Source Reference**: `customer_objections_faq.md#section_5`
- **Similarity Score**: `0.9290`
- **Verdict**: **CORRECT**
- **Relevance Explanation**: Retrieved exact target record 'kb_custom_005' (FAQ 4: "What happens if my business revenue temporarily dips?"). Matched critical domain facts: ['seasonality', 'payment relief', 'restructuring', '10 business days'] with hybrid similarity score of 0.9290.

### TEST_05_OBJECTION
- **User Question**: *"Why is your interest rate higher than traditional tier-1 commercial banks?"*
- **Retrieved Record**: `kb_custom_002` — **Objection 1: "Why is your Nominal Interest Rate higher than traditional tier-1 commercial banks?"**
- **Source Reference**: `customer_objections_faq.md#section_2`
- **Similarity Score**: `0.9122`
- **Verdict**: **CORRECT**
- **Relevance Explanation**: Retrieved exact target record 'kb_custom_002' (Objection 1: "Why is your Nominal Interest Rate higher than traditional tier-1 commercial banks?"). Matched critical domain facts: ['unsecured financing', '24 to 48 hours', 'real estate collateral'] with hybrid similarity score of 0.9122.
