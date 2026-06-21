import re
from typing import Dict, Any, Tuple, Optional

class ResponseValidator:
    def __init__(self):
        # Scan for advisory/compliance forbidden patterns in final output
        self.advisory_patterns = [
            r"\b(?:recommend|suggest|advice|advisable|should\s+invest|safe|risky)\b",
            r"\b(?:better\s+option|best\s+option|buy\b|sell\b|hold\b)"
        ]
        self.advisory_regex = [re.compile(p, re.IGNORECASE) for p in self.advisory_patterns]
        
        # Allowed corpus URLs
        self.allowed_urls = [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
            "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
            "https://www.amfiindia.com/investor/knowledge-center-info?faqs",
            "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&cid=1"
        ]

    def split_sentences(self, text: str) -> list:
        # Split on period, question mark, or exclamation followed by space
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    def enforce_sentence_limit(self, text: str, max_sentences: int = 3) -> str:
        sentences = self.split_sentences(text)
        if len(sentences) <= max_sentences:
            return text
        return " ".join(sentences[:max_sentences])

    def check_advisory_leak(self, text: str) -> bool:
        # Returns True if advisory leak is detected
        text_lower = text.lower()
        for rx in self.advisory_regex:
            if rx.search(text_lower):
                return True
        return False

    def verify_grounding(self, answer: str, context_str: str) -> bool:
        # Performs factual grounding validation on numeric values mentioned in LLM answer
        # Find all percentages (e.g. 0.73%) and numbers associated with currency or ratios
        numbers = re.findall(r"\b\d+\.?\d*%\b|\b₹?\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", answer)
        
        # Remove small numbers like 1, 2, 3 sentences or simple indices to avoid false positives
        filtered_numbers = []
        for n in numbers:
            # If it's a percentage, currency, or contains a decimal point, keep it as it's a financial fact
            if "%" in n or "₹" in n or "." in n:
                filtered_numbers.append(n)
                continue
                
            val_str = n.replace("₹", "").replace("%", "").replace(",", "")
            try:
                val = float(val_str)
                # Ignore common small integers like sentence bounds (1, 2, 3, etc.)
                if val.is_integer() and val <= 5:
                    continue
                filtered_numbers.append(n)
            except ValueError:
                pass

        # Check if each number in the answer exists in the context text
        context_str_clean = context_str.replace("₹", "").replace("%", "").replace(",", "")
        for num in filtered_numbers:
            num_clean = num.replace("₹", "").replace("%", "").replace(",", "")
            if num_clean not in context_str_clean:
                print(f"Grounding violation: Fact '{num}' is not present in the retrieved context.")
                return False
        return True

    def validate(self, raw_answer: str, context_str: str, default_citation: str) -> Tuple[str, str, bool]:
        # Perform comprehensive checks. Returns (answer, citation_url, is_refusal)
        
        # 1. Truncate response to max 3 sentences
        answer = self.enforce_sentence_limit(raw_answer, max_sentences=3)

        # 2. Check for information failure pattern
        if "information not found" in answer.lower() or "not found in official" in answer.lower():
            return "Information not found in official source files.", default_citation, False

        # 3. Check for advisory leakage
        if self.check_advisory_leak(answer):
            print(f"Validation failure: Advisory leak detected in answer: '{answer}'")
            return (
                "I am a facts-only mutual fund FAQ assistant. I cannot provide investment advice or suggestions on whether you should buy or sell a fund.",
                "https://www.amfiindia.com/investor/knowledge-center-info?faqs",
                True
            )

        # 4. Check factual grounding
        if not self.verify_grounding(answer, context_str):
            return "Information not found in official source files.", default_citation, False

        # 5. Check citation URL allowlist
        citation_url = default_citation
        if citation_url not in self.allowed_urls:
            citation_url = "https://www.amfiindia.com/investor/knowledge-center-info?faqs"

        return answer, citation_url, False
