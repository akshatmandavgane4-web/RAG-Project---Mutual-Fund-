import re
import json
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "corpus.yaml"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

class Parser:
    def __init__(self, config_path: Path = CONFIG_PATH, raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR):
        self.config_path = config_path
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def parse_file(self, file_path: Path, scheme_meta: dict) -> dict:
        html_content = file_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Prepare raw clean text for regex matches
        # Temp clean scripts & style to extract base readable text
        soup_copy = BeautifulSoup(html_content, "html.parser")
        for s in soup_copy(["script", "style"]):
            s.extract()
        raw_text = re.sub(r'\s+', ' ', soup_copy.get_text())

        # Extract structured parameters from HTML & JSON-LD
        expense_ratio = "N/A"
        aum = "N/A"
        nav = "N/A"
        
        # Match from JSON-LD
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(s.string)
                if isinstance(data, dict):
                    # Product schema
                    if data.get("@type") == "Product":
                        pass
                    # FAQPage schema
                    if data.get("@type") == "FAQPage":
                        for q in data.get("mainEntity", []):
                            qname = q.get("name", "")
                            qans = q.get("acceptedAnswer", {}).get("text", "")
                            ans_text = BeautifulSoup(qans, "html.parser").get_text()
                            
                            if "AUM" in qname or "AUM" in ans_text:
                                m_aum = re.search(r"is\s*[^0-9\s]*\s*([\d,]+\.?\d*\s*(?:Cr|Crore))", ans_text, re.IGNORECASE)
                                if m_aum:
                                    aum = "₹" + m_aum.group(1).strip()
                            
                            if "expense ratio" in qname.lower() or "expense ratio" in ans_text.lower():
                                m_exp = re.search(r"is\s*(\d+\.\d+%)", ans_text, re.IGNORECASE)
                                if m_exp:
                                    expense_ratio = m_exp.group(1)
                                    
                            if "NAV" in qname or "NAV" in ans_text:
                                m_nav = re.search(r"is\s*[^0-9\s]*\s*([\d,]+\.?\d*)", ans_text, re.IGNORECASE)
                                if m_nav:
                                    nav = "₹" + m_nav.group(1).strip()
            except Exception:
                pass

        # Fallbacks using regex on raw text
        if expense_ratio == "N/A":
            m = re.search(r"Expense ratio.*?(\d+\.\d+%)", raw_text, re.IGNORECASE)
            if m:
                expense_ratio = m.group(1)
            else:
                # Match simple decimal followed by percentage
                m2 = re.search(r"Expense Ratio\s*(\d+\.\d+%)", raw_text, re.IGNORECASE)
                if m2:
                    expense_ratio = m2.group(1)

        if nav == "N/A":
            # Match NAV value patterns (e.g. NAV: ₹123.45 or NAV: 123.45)
            m = re.search(r"NAV\s*(?:as of \d+ [A-Za-z]+ '\d+)?\s*₹?\s*([\d,]+\.\d+)", raw_text, re.IGNORECASE)
            if m:
                nav = "₹" + m.group(1)

        if aum == "N/A":
            # Match AUM patterns (e.g. Fund size (AUM) ₹12,345.67 Cr)
            m = re.search(r"(?:Fund size|AUM)\s*\(?AUM\)?\s*₹?\s*([\d,]+\.?\d*\s*(?:Cr|Crore))", raw_text, re.IGNORECASE)
            if m:
                aum = "₹" + m.group(1)

        # Min SIP
        min_sip = 100.0
        m_sip = re.search(r"Minimum SIP Investment is set to\s*₹?(\d+)", raw_text, re.IGNORECASE)
        if m_sip:
            min_sip = float(m_sip.group(1))
        else:
            m_sip2 = re.search(r"(?:Min\. for SIP|Minimum SIP)\s*₹?\s*(\d+)", raw_text, re.IGNORECASE)
            if m_sip2:
                min_sip = float(m_sip2.group(1))

        # Exit Load
        exit_load = "N/A"
        all_exits = re.findall(r"Exit\s+load\s+(.*?)(?=\.|\;|\n|Stamp\s+duty|AUM|$)", raw_text, re.IGNORECASE)
        if all_exits:
            exit_load = all_exits[-1].strip()
            if exit_load.lower().startswith("of "):
                exit_load = exit_load[3:].strip()
            if exit_load.lower().startswith("for "):
                exit_load = exit_load.strip()
            if exit_load.endswith("."):
                exit_load = exit_load[:-1]

        # Riskometer
        riskometer = "Very High"
        m_risk = re.search(r"rated\s+([A-Za-z\s\-]+)\s+risk", raw_text, re.IGNORECASE)
        if m_risk:
            riskometer = m_risk.group(1).strip().title()

        # Benchmark
        benchmark = "N/A"
        m_bench = re.search(r"(?:Fund benchmark|Benchmark index)\s*(.*?)(?:Scheme|Information|$)", raw_text, re.IGNORECASE)
        if m_bench:
            benchmark = m_bench.group(1).strip()

        # Fund Managers
        managers = []
        # Attempt to parse fund managers block
        m_mgr = re.findall(r"Compare Fund management|Fund management\s*(.*?)(?=\bEducation\b|$)", raw_text, re.IGNORECASE)
        # We also look for specific fund manager name headers and details
        # Let's extract blocks related to managers and construct their detail
        mgr_matches = re.finditer(r"([A-Z][A-Za-z\s\']+)\s+(\w{3}\s+\d{4}\s*-\s*(?:Present|\w{3}\s+\d{4}))", raw_text)
        for match in mgr_matches:
            name = match.group(1).strip()
            tenure = match.group(2).strip()
            
            # Extract background info
            sub_text = raw_text[match.end():match.end() + 600]
            edu_m = re.search(r"Education\s*(.*?)(?:Experience|Also manages|$)", sub_text, re.IGNORECASE)
            exp_m = re.search(r"Experience\s*(.*?)(?:Also manages|View details|$)", sub_text, re.IGNORECASE)
            
            bg = ""
            if edu_m:
                bg += "Education: " + edu_m.group(1).strip()
            if exp_m:
                if bg:
                    bg += " | "
                bg += "Experience: " + exp_m.group(1).strip()
                
            if name not in [m["name"] for m in managers]:
                managers.append({
                    "name": name,
                    "tenure": tenure,
                    "background": bg or "N/A"
                })

        if not managers:
            managers.append({
                "name": "N/A",
                "tenure": "N/A",
                "background": "N/A"
            })

        # 2. Extract Sections for RAG text grounding
        sections = {
            "overview": "",
            "expense_ratio": "",
            "exit_load": "",
            "minimum_investment": "",
            "benchmark": "",
            "tax": "",
            "fund_management": "",
            "investment_objective": "",
            "fund_house": ""
        }

        # Sub-strings parsing for sections using sliding regex windows or keyword regions
        # Expense Ratio
        m_exp_sec = re.search(r"(?:Expense ratio|Expense Ratio)(.*?)(?:Rating|Min\. for SIP|Exit load|$)", raw_text, re.IGNORECASE)
        if m_exp_sec:
            sections["expense_ratio"] = f"Expense Ratio information: {m_exp_sec.group(0).strip()}"
        
        # Exit Load
        m_exit_sec = re.search(r"(?:Exit Load|Exit load)(.*?)(?:Tax implication|Compare similar|$)", raw_text, re.IGNORECASE)
        if m_exit_sec:
            sections["exit_load"] = f"Exit Load information: {m_exit_sec.group(0).strip()}"

        # Minimum Investment
        m_min_sec = re.search(r"(?:Minimum investments|Min\. for 1st investment)(.*?)(?:Returns and rankings|Expense ratio|$)", raw_text, re.IGNORECASE)
        if m_min_sec:
            sections["minimum_investment"] = f"Minimum Investment details: {m_min_sec.group(0).strip()}"

        # Benchmark
        m_bench_sec = re.search(r"(?:Fund benchmark|Benchmark index)(.*?)(?:Scheme Information|$)", raw_text, re.IGNORECASE)
        if m_bench_sec:
            sections["benchmark"] = f"Benchmark Index details: {m_bench_sec.group(0).strip()}"

        # Tax
        m_tax_sec = re.search(r"(?:Tax implication|Taxation details)(.*?)(?:Check past data|Compare similar|$)", raw_text, re.IGNORECASE)
        if m_tax_sec:
            sections["tax"] = f"Tax implications: {m_tax_sec.group(0).strip()}"

        # Fund Management
        m_mgr_sec = re.search(r"(?:Compare Fund management|Fund management)(.*?)(?:About |$)", raw_text, re.IGNORECASE)
        if m_mgr_sec:
            sections["fund_management"] = f"Fund Management profiles: {m_mgr_sec.group(0).strip()}"

        # Investment Objective
        m_obj_sec = re.search(r"(?:Investment Objective|Investment objective)(.*?)(?:Fund benchmark|$)", raw_text, re.IGNORECASE)
        if m_obj_sec:
            sections["investment_objective"] = f"Investment Objective: {m_obj_sec.group(0).strip()}"

        # Fund House
        m_house_sec = re.search(r"(?:Fund house|About the AMC)(.*?)(?=$)", raw_text, re.IGNORECASE)
        if m_house_sec:
            sections["fund_house"] = f"Fund House (AMC) details: {m_house_sec.group(0).strip()}"

        # Overview fallback
        m_ov_sec = re.search(r"(?:About HDFC|About HDFC Mutual Fund|About HDFC Prudential)(.*?)(?:Investment Objective|$)", raw_text, re.IGNORECASE)
        if m_ov_sec:
            sections["overview"] = f"Overview: {m_ov_sec.group(0).strip()}"
        else:
            # Short paragraph mapping
            sections["overview"] = f"Overview of {scheme_meta['name']}: The fund category is {scheme_meta['category']}. Latest NAV is {nav} and Asset Under Management (AUM) size is {aum}."

        # Clean up all section texts to replace incorrect total AMC AUM with scheme-specific AUM
        wrong_aum_pattern = r"Asset\s+Under\s+Management\s*\(?AUM\)?\s+of\s+[^a-zA-Z0-9]*\s*[\d,]+(?:\.\d+)?\s*(?:Cr|Crore)?"
        for key in sections:
            if sections[key]:
                sections[key] = re.sub(
                    wrong_aum_pattern,
                    f"Asset Under Management(AUM) of {aum}",
                    sections[key],
                    flags=re.IGNORECASE
                )

        return {
            "metadata": {
                "id": scheme_meta["slug"],
                "name": scheme_meta["name"],
                "source_url": scheme_meta["source_url"],
                "expense_ratio": expense_ratio,
                "exit_load": exit_load,
                "min_sip": min_sip,
                "riskometer_class": riskometer,
                "benchmark_index": benchmark,
                "fund_managers": managers,
                "nav": nav,
                "aum": aum,
                "category": scheme_meta["category"],
                "last_updated": datetime.today().strftime("%Y-%m-%d")
            },
            "sections": sections
        }

    def run(self):
        try:
            config_data = self.load_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return

        schemes = config_data.get("schemes", [])
        parsed_results = []

        for scheme in schemes:
            slug = scheme["slug"]
            file_path = self.raw_dir / f"{slug}.html"
            
            if not file_path.exists():
                print(f"Raw HTML file not found for {slug}, skipping parsing.")
                continue
            
            try:
                print(f"Parsing {file_path.name}...")
                parsed_data = self.parse_file(file_path, scheme)
                parsed_results.append(parsed_data)
                
                # Write individual processed JSON file
                out_path = self.processed_dir / f"{slug}.json"
                with open(out_path, "w", encoding="utf-8") as out_f:
                    json.dump(parsed_data, out_f, indent=2)
                print(f"Successfully wrote parsed scheme to {out_path}")
            except Exception as e:
                print(f"Error parsing scheme {slug}: {e}")

        # Also write a combined dataset for simplicity
        combined_path = self.processed_dir / "schemes_parsed.json"
        with open(combined_path, "w", encoding="utf-8") as comb_f:
            json.dump(parsed_results, comb_f, indent=2)
        print(f"Combined parsed schemes saved to {combined_path}")

if __name__ == "__main__":
    parser = Parser()
    parser.run()
