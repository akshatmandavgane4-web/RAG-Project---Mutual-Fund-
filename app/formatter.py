from typing import Dict, Any

class ResponseFormatter:
    @staticmethod
    def format_response(answer: str, citation_url: str, last_updated: str, is_refusal: bool) -> Dict[str, Any]:
        # Formulate structured JSON response payload mapping to API specifications
        
        # Append "Last updated from sources: <date>" footer if not already present in text
        # If it's a refusal, we can use the default timestamp
        footer_date = last_updated or "2026-06-17"
        
        return {
            "answer": answer,
            "citation_url": citation_url,
            "last_updated": footer_date,
            "is_refusal": is_refusal,
            "disclaimer": "Facts-only. No investment advice."
        }
