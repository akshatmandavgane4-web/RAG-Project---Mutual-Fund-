import re
from typing import Dict, Any, Tuple, Optional

class QueryClassifier:
    def __init__(self):
        # 1. PII Scan Patterns
        # PAN: 5 letters, 4 digits, 1 letter
        self.pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
        # Aadhaar: 12 digits, optional spaces/hyphens
        self.aadhaar_pattern = re.compile(r"\b[2-9]{1}[0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b")
        # Email RFC 5322 pattern
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        # Phone: 10 digits, optional country code +91
        self.phone_pattern = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")
        # Generic bank account / OTP structures
        self.otp_pattern = re.compile(r"\b\d{4,6}\b.*\botp\b|\botp\b.*\b\d{4,6}\b", re.IGNORECASE)

        # 2. Intent Patterns
        # Advisory
        self.advisory_patterns = [
            r"should\s+i\s+(?:invest|buy|sell|choose|get|put|hold|trade)",
            r"is\s+this\s+fund\s+(?:good|bad|safe|risky|worth|suitable|for\s+me)",
            r"suggest\s+a\s+fund",
            r"recommend\b",
            r"help\s+me\s+choose",
            r"buy\s+or\s+sell"
        ]
        self.advisory_regex = [re.compile(p, re.IGNORECASE) for p in self.advisory_patterns]

        # Comparison
        self.comparison_patterns = [
            r"which\s+.*?(?:better|best|worse|top)",
            r"\bvs\b",
            r"compare\s+funds",
            r"difference\s+between"
        ]
        self.comparison_regex = [re.compile(p, re.IGNORECASE) for p in self.comparison_patterns]

        # Performance-seeking
        self.performance_patterns = [
            r"\breturns?\b.*?\b(?:forecast|prediction|calculate|get|project|predict)",
            r"\b(?:predict|forecast|calculate|project)\b.*?\breturns?\b",
            r"future\s+returns",
            r"compare\s+(?:3y|1y|5y|returns)",
            r"will\s+this\s+fund\s+(?:make|grow|give)\b"
        ]
        self.performance_regex = [re.compile(p, re.IGNORECASE) for p in self.performance_patterns]

        # Supported scheme keywords for scope checking
        self.scheme_keywords = {
            "hdfc-mid-cap-fund-direct-growth": ["mid cap", "midcap"],
            "hdfc-large-cap-fund-direct-growth": ["large cap", "largecap"],
            "hdfc-small-cap-fund-direct-growth": ["small cap", "smallcap"],
            "hdfc-gold-etf-fund-of-fund-direct-plan-growth": ["gold", "etf", "gold fof"],
            "hdfc-defence-fund-direct-growth": ["defence", "defense"]
        }

    def scan_for_pii(self, query: str) -> Tuple[bool, Optional[str]]:
        # Scan for PII violations. Returns (is_pii_detected, redacted_text)
        redacted = query
        has_pii = False

        if self.pan_pattern.search(redacted):
            has_pii = True
            redacted = self.pan_pattern.sub("[PAN REDACTED]", redacted)
        if self.aadhaar_pattern.search(redacted):
            has_pii = True
            redacted = self.aadhaar_pattern.sub("[AADHAAR REDACTED]", redacted)
        if self.email_pattern.search(redacted):
            has_pii = True
            redacted = self.email_pattern.sub("[EMAIL REDACTED]", redacted)
        if self.phone_pattern.search(redacted):
            has_pii = True
            redacted = self.phone_pattern.sub("[PHONE REDACTED]", redacted)
        if self.otp_pattern.search(redacted):
            has_pii = True
            redacted = "[SENSITIVE OTP BLOCKED]"

        return has_pii, redacted

    def classify_intent(self, query: str) -> str:
        # Categorize query into label: factual, advisory, comparison, performance, out_of_scope
        query_lower = query.lower()

        # 1. Check Advisory intent
        for rx in self.advisory_regex:
            if rx.search(query_lower):
                return "advisory"

        # 2. Check Comparison intent
        for rx in self.comparison_regex:
            if rx.search(query_lower):
                return "comparison"

        # 3. Check Performance intent
        for rx in self.performance_regex:
            if rx.search(query_lower):
                return "performance"

        # 4. Check Out of Scope (does not refer to any of the 5 HDFC schemes in our corpus, or asks unrelated general topics)
        # Note: If they query general greeting or small talk, we handle it as out of scope.
        is_hdfc_query = "hdfc" in query_lower or any(
            any(kw in query_lower for kw in keywords)
            for keywords in self.scheme_keywords.values()
        )
        if not is_hdfc_query:
            # Let general greetings flow if they match factual structure, but route general unrelated things to out of scope
            factual_tokens = ["expense ratio", "exit load", "sip", "benchmark", "manager", "nav", "aum"]
            has_factual_token = any(tok in query_lower for tok in factual_tokens)
            if not has_factual_token:
                return "out_of_scope"

        return "factual"

    def handle_refusal(self, intent: str, pii_detected: bool = False) -> Dict[str, Any]:
        # Generate standardized polite compliance refusals with educational links
        if pii_detected:
            return {
                "answer": "Sensitive personal data detected. Please query without sharing personal numbers, emails, or credentials.",
                "citation_url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&cid=1",
                "last_updated": "2026-06-17",
                "is_refusal": True
            }

        if intent == "advisory":
            return {
                "answer": "I am a facts-only mutual fund FAQ assistant. I cannot provide investment advice or suggestions on whether you should buy or sell a fund.",
                "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?faqs",
                "last_updated": "2026-06-17",
                "is_refusal": True
            }
        
        if intent == "comparison":
            return {
                "answer": "I cannot perform comparison reviews or advise which mutual fund is better. Please check the individual fund details or consult a registered advisor.",
                "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?faqs",
                "last_updated": "2026-06-17",
                "is_refusal": True
            }

        if intent == "performance":
            return {
                "answer": "I cannot compute hypothetical returns or project future performance values. Past performance is not indicative of future returns.",
                "citation_url": "https://www.amfiindia.com/investor/knowledge-center-info?faqs",
                "last_updated": "2026-06-17",
                "is_refusal": True
            }

        # Out of Scope / Default
        return {
            "answer": "I can only answer factual questions about the 5 target HDFC mutual fund schemes in my corpus (Mid Cap, Large Cap, Small Cap, Gold ETF FoF, and Defence Fund).",
            "citation_url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&cid=1",
            "last_updated": "2026-06-17",
            "is_refusal": True
        }

if __name__ == "__main__":
    classifier = QueryClassifier()
    # PII test
    pii, red = classifier.scan_for_pii("My PAN is ABCDE1234F. What is the exit load?")
    print(f"PII: {pii}, Redacted: {red}")
    # Advisory test
    intent = classifier.classify_intent("Should I invest in HDFC Mid Cap?")
    print(f"Intent: {intent}, Refusal: {classifier.handle_refusal(intent)}")
