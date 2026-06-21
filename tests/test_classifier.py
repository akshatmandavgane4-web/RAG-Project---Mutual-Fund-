import pytest
from app.classifier import QueryClassifier

def test_pii_scanning():
    classifier = QueryClassifier()
    
    # PAN Scan
    has_pii, redacted = classifier.scan_for_pii("My PAN code is ABCDE1234F. What is the SIP?")
    assert has_pii is True
    assert "[PAN REDACTED]" in redacted
    assert "ABCDE1234F" not in redacted
    
    # Aadhaar Scan
    has_pii, redacted = classifier.scan_for_pii("My Aadhaar is 5555 4444 3333.")
    assert has_pii is True
    assert "[AADHAAR REDACTED]" in redacted
    
    # Email Scan
    has_pii, redacted = classifier.scan_for_pii("Email support at info@hdfcfund.com")
    assert has_pii is True
    assert "[EMAIL REDACTED]" in redacted

    # Phone Scan
    has_pii, redacted = classifier.scan_for_pii("Contact me at +91 9999988888")
    assert has_pii is True
    assert "[PHONE REDACTED]" in redacted

    # Clean query
    has_pii, redacted = classifier.scan_for_pii("What is the expense ratio of HDFC Mid Cap?")
    assert has_pii is False
    assert redacted == "What is the expense ratio of HDFC Mid Cap?"

def test_intent_classification():
    classifier = QueryClassifier()

    # Factual Queries
    assert classifier.classify_intent("What is the expense ratio of HDFC Defence Fund?") == "factual"
    assert classifier.classify_intent("Who manages HDFC Small Cap?") == "factual"
    
    # Advisory Queries
    assert classifier.classify_intent("Should I invest in HDFC Mid Cap?") == "advisory"
    assert classifier.classify_intent("Recommend a good mutual fund to buy") == "advisory"

    # Comparison Queries
    assert classifier.classify_intent("Which is better: HDFC Mid Cap or HDFC Large Cap?") == "comparison"
    assert classifier.classify_intent("HDFC Small Cap vs HDFC Defence Fund") == "comparison"

    # Performance Queries
    assert classifier.classify_intent("Predict the returns of HDFC Defence Fund for next year") == "performance"
    assert classifier.classify_intent("HDFC Large Cap returns forecast") == "performance"

    # Out of Scope Queries
    assert classifier.classify_intent("What is the weather in Delhi?") == "out_of_scope"
    assert classifier.classify_intent("Tell me a joke") == "out_of_scope"

def test_refusal_handlers():
    classifier = QueryClassifier()
    
    advisory_res = classifier.handle_refusal("advisory")
    assert advisory_res["is_refusal"] is True
    assert "cannot provide investment advice" in advisory_res["answer"]
    assert advisory_res["citation_url"] == "https://www.amfiindia.com/investor/knowledge-center-info?faqs"
    
    pii_res = classifier.handle_refusal("factual", pii_detected=True)
    assert pii_res["is_refusal"] is True
    assert "personal data detected" in pii_res["answer"]
