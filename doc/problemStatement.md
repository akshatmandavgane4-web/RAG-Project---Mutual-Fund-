# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as Asset Management Company (AMC) websites, AMFI, and SEBI.

> [!IMPORTANT]
> The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective
Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that:
- Answers factual queries about mutual fund schemes.
- Uses a curated corpus of official documents.
- Provides concise, source-backed responses.

---

## Target Users
- **Retail Investors:** Users comparing mutual fund schemes.
- **Customer Support & Content Teams:** Teams handling repetitive mutual fund queries.

---

## Scope of Work

### 1. Corpus Definition
- **Selected AMC:** ICICI Prudential Mutual Fund
- **Scope Limit:** Currently limited to the following **5 target URLs** (Groww scheme pages):
  - [ICICI Prudential Large Cap Fund Direct Growth](https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth)
  - [ICICI Prudential Silver ETF FoF Direct Growth](https://groww.in/mutual-funds/icici-prudential-silver-etf-fof-direct-growth)
  - [ICICI Prudential Dynamic Plan Direct Growth](https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth)
  - [ICICI Prudential Infrastructure Fund Direct Growth](https://groww.in/mutual-funds/icici-prudential-infrastructure-fund-direct-growth)
  - [ICICI Prudential Balanced Direct Growth](https://groww.in/mutual-funds/icici-prudential-balanced-direct-growth)

### 2. FAQ Assistant Requirements
The assistant must:
- **Answer facts-only queries**, such as:
  - Expense ratio of a scheme
  - Exit load details
  - Minimum SIP amount
  - ELSS lock-in period
  - Riskometer classification
  - Benchmark index
  - Fund management details (e.g., fund managers, tenure, and background)
  - Process to download statements or capital gains reports
- **Ensure Constraints are Met:**
  - Each response is limited to a maximum of **3 sentences**.
  - Each response includes **exactly one** citation link.
  - Each response includes a footer:
    > *Last updated from sources: &lt;date&gt;*

### 3. Refusal Handling
The assistant must refuse non-factual or advisory queries, such as *"Should I invest in this fund?"* or *"Which fund is better?"*.
- **Refusal responses should:**
  - Be polite and clearly worded.
  - Reinforce the facts-only limitation.
  - Provide a relevant educational link (e.g., AMFI or SEBI resource).

### 4. User Interface (Minimal)
The solution should include a simple interface with:
- A welcome message
- Three example questions
- A visible disclaimer:
  > **Facts-only. No investment advice.**

---

## Constraints

| Category | Description / Constraint Rule |
| :--- | :--- |
| **Data and Sources** | Use **only** official public sources (AMC, AMFI, SEBI). Do not use third-party blogs or aggregator websites. |
| **Privacy and Security** | Do **not** collect, store, or process: PAN or Aadhaar numbers, account numbers, OTPs, email addresses, or phone numbers. |
| **Content Restrictions** | No investment advice or recommendations. No performance comparisons or return calculations. For performance-related queries, provide a link to the official factsheet only. |
| **Transparency** | Responses must be short, factual, and verifiable. Every answer must include a source link and the last updated date. |

---

## Expected Deliverables
- **README Document:**
  - Setup instructions
  - Selected AMC and schemes
  - Architecture overview (RAG approach)
  - Known limitations
- **Disclaimer Snippet:**
  > *“Facts-only. No investment advice.”*

---

## Success Criteria
- [ ] **Accurate Retrieval:** Accurate retrieval of factual mutual fund information.
- [ ] **Facts-Only Adherence:** Strict adherence to facts-only responses (no opinion/advice).
- [ ] **Valid Citations:** Consistent inclusion of valid source citations.
- [ ] **Advisory Refusal:** Proper refusal of advisory queries.
- [ ] **Clean Interface:** Clean, minimal, and user-friendly interface.

---

## Summary
The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
