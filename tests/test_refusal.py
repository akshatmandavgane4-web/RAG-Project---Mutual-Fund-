import pytest
from app.classifier import QueryClassifier
from app.validator import ResponseValidator
from app.formatter import ResponseFormatter

def test_pii_detection_refusal():
    classifier = QueryClassifier()
    
    # Check Aadhaar number trigger
    query_aadhaar = "My Aadhaar number is 2345-6789-0123. What is the AUM of HDFC Mid Cap?"
    has_pii, redacted = classifier.scan_for_pii(query_aadhaar)
    assert has_pii is True
    assert "[AADHAAR REDACTED]" in redacted
    
    # Assert refusal response format for PII
    res = classifier.handle_refusal("factual", pii_detected=True)
    assert res["is_refusal"] is True
    assert "Sensitive personal data detected" in res["answer"]
    assert res["citation_url"] == "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&cid=1"

def test_intent_classification_refusals():
    classifier = QueryClassifier()
    
    # Advisory Intent Block
    query_advisory = "Should I buy HDFC Large Cap fund?"
    intent = classifier.classify_intent(query_advisory)
    assert intent == "advisory"
    res = classifier.handle_refusal(intent)
    assert res["is_refusal"] is True
    assert "cannot provide investment advice" in res["answer"]
    assert res["citation_url"] == "https://www.amfiindia.com/investor/knowledge-center-info?faqs"
    
    # Comparison Intent Block
    query_comp = "Compare HDFC Small Cap vs HDFC Mid Cap returns."
    intent = classifier.classify_intent(query_comp)
    assert intent == "comparison"
    res = classifier.handle_refusal(intent)
    assert res["is_refusal"] is True
    assert "cannot perform comparison reviews" in res["answer"]
    
    # Performance Intent Block
    query_perf = "Can you project the future returns for HDFC Defence Fund?"
    intent = classifier.classify_intent(query_perf)
    assert intent == "performance"
    res = classifier.handle_refusal(intent)
    assert res["is_refusal"] is True
    assert "cannot compute hypothetical returns" in res["answer"]

    # Out of Scope Intent Block
    query_oos = "Who won the football world cup?"
    intent = classifier.classify_intent(query_oos)
    assert intent == "out_of_scope"
    res = classifier.handle_refusal(intent)
    assert res["is_refusal"] is True
    assert "can only answer factual questions about the 5 target HDFC mutual fund schemes" in res["answer"]

def test_validator_advisory_leak_refusal():
    validator = ResponseValidator()
    
    # Mock LLM response with advisory leak
    raw_answer = "The exit load of HDFC Large Cap is 1.0% if redeemed within 1 year. I suggest this is a safe option for short term."
    context_str = "The exit load is 1.0% for redemption within 365 days."
    default_citation = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    
    answer, citation, is_refusal = validator.validate(raw_answer, context_str, default_citation)
    
    assert is_refusal is True
    assert "I am a facts-only mutual fund FAQ assistant" in answer
    assert citation == "https://www.amfiindia.com/investor/knowledge-center-info?faqs"

def test_validator_grounding_violation_refusal():
    validator = ResponseValidator()
    
    # Mock LLM response mentioning a metric/number not in context
    raw_answer = "HDFC Mid Cap Fund has an expense ratio of 0.85%."
    context_str = "Scheme: HDFC Mid Cap | Expense Ratio: 0.73% | NAV: 154.2"
    default_citation = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    
    answer, citation, is_refusal = validator.validate(raw_answer, context_str, default_citation)
    
    # Grounding violation should result in "Information not found" fallback response
    assert is_refusal is False
    assert answer == "Information not found in official source files."
    assert citation == default_citation

def test_validator_compliant_response():
    validator = ResponseValidator()
    
    raw_answer = "The expense ratio is 0.73% for the direct growth option."
    context_str = "Scheme: HDFC Mid Cap | Expense Ratio: 0.73% | NAV: 154.2"
    default_citation = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    
    answer, citation, is_refusal = validator.validate(raw_answer, context_str, default_citation)
    
    assert is_refusal is False
    assert answer == raw_answer
    assert citation == default_citation
