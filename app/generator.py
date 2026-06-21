import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class RAGGenerator:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "150"))

        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: LLM_API_KEY is not configured in env.")

        self.system_prompt = (
            "You are a compliant, facts-only Mutual Fund FAQ Assistant.\n"
            "Your objective is to answer user queries using exclusively the provided Context.\n"
            "Adhere strictly to these rules:\n"
            "1. Answer factual queries only. No opinions, investment advice, or future return projections.\n"
            "2. Never recommend a scheme or compare fund returns. If performance is queried, refuse to calculate and direct the user to check the official factsheet.\n"
            "3. Limit your response to a maximum of 3 sentences.\n"
            "4. Do not include citation links or URLs inside your response text (these will be attached dynamically by the engine).\n"
            "5. Answer directly. Do not include introductory pleasantries (like 'Sure, here is...'), conversational filler, or meta-notes.\n"
            "6. If the answer cannot be completely constructed from the Context, reply exactly with: 'Information not found in official source files.'"
        )

    def build_context_string(self, resolved_scheme_metadata: Optional[dict], chunks: list) -> str:
        context_parts = []
        
        # 1. Add structured scheme metadata if resolved
        if resolved_scheme_metadata:
            managers = resolved_scheme_metadata.get("fund_managers", [])
            mgr_str = ", ".join([f"{m['name']} (Tenure: {m['tenure']}, BG: {m['background']})" for m in managers])
            
            scheme_info = (
                f"Scheme Name: {resolved_scheme_metadata.get('name')}\n"
                f"Category: {resolved_scheme_metadata.get('category')}\n"
                f"Expense Ratio: {resolved_scheme_metadata.get('expense_ratio')}\n"
                f"Exit Load: {resolved_scheme_metadata.get('exit_load')}\n"
                f"Minimum SIP: ₹{resolved_scheme_metadata.get('min_sip')}\n"
                f"Riskometer Rating: {resolved_scheme_metadata.get('riskometer_class')} Risk\n"
                f"Benchmark Index: {resolved_scheme_metadata.get('benchmark_index')}\n"
                f"NAV: {resolved_scheme_metadata.get('nav')}\n"
                f"AUM: {resolved_scheme_metadata.get('aum')}\n"
                f"Current Fund Managers: {mgr_str}\n"
                f"Source Page: {resolved_scheme_metadata.get('source_url')}"
            )
            context_parts.append(scheme_info)

        # 2. Add unstructured chunk text contents
        for chunk in chunks:
            # Check if chunk is dict structure or object
            text_content = chunk.get("text") if isinstance(chunk, dict) else getattr(chunk, "text", "")
            if text_content:
                context_parts.append(f"Content Passage: {text_content}")

        return "\n===\n".join(context_parts)

    def generate(self, query: str, resolved_scheme_metadata: Optional[dict], chunks: list) -> str:
        if not self.client:
            raise ValueError("Groq client not initialized (missing API key)")

        context_string = self.build_context_string(resolved_scheme_metadata, chunks)
        user_content = (
            f"Context:\n{context_string}\n\n"
            f"User Query: {query}"
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during Groq API completion: {e}")
            raise
