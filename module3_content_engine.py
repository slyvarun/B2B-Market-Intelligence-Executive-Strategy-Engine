import os
import sys
import uuid
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from pydantic import BaseModel, Field
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


class ContentSectionSchema(BaseModel):
    header: str = Field(description="Section heading")
    key_takeaways: List[str] = Field(description="Executive takeaways for decision makers")
    executive_summary: str = Field(description="Detailed narrative section summary")


class SEOStrategySchema(BaseModel):
    meta_description: str = Field(description="Meta description for search engines")
    primary_keywords: List[str] = Field(description="Primary keywords")
    secondary_keywords: List[str] = Field(description="Secondary keywords")
    url_slug: str = Field(description="URL slug")


class AEOGEOStrategySchema(BaseModel):
    direct_answer_snippet: str = Field(description="Direct answer snippet for AI search engines")
    citable_facts: List[str] = Field(description="Citable statistical figures and facts")
    ai_engine_keywords: List[str] = Field(description="Keywords for LLM retrieval")
    entity_tags: List[str] = Field(description="Entity tags")


class FAQItemSchema(BaseModel):
    question: str = Field(description="Executive question")
    optimized_answer: str = Field(description="Optimized answer")


class CTASchema(BaseModel):
    cta_headline: str = Field(description="CTA headline")
    cta_button_text: str = Field(description="Button label text")
    cta_type: str = Field(description="CTA strategy type")


class ContentBlueprintSchema(BaseModel):
    proposed_title: str = Field(description="Report title")
    executive_target_audience: List[str] = Field(description="Target executive personas")
    seo_strategy: SEOStrategySchema
    aeo_geo_strategy: AEOGEOStrategySchema
    content_outline: List[ContentSectionSchema]
    faq_structures: List[FAQItemSchema]
    call_to_action: CTASchema


@dataclass
class ContentBlueprint:
    blueprint_id: str
    opportunity_id: str
    industry: str
    keyword: str
    target_country: str
    executive_target_audience: List[str]
    proposed_title: str
    seo_strategy: Dict[str, Any]
    aeo_geo_strategy: Dict[str, Any]
    content_outline: List[Dict[str, Any]]
    faq_structures: List[Dict[str, Any]]
    call_to_action: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "opportunity_id": self.opportunity_id,
            "industry": self.industry,
            "keyword": self.keyword,
            "target_country": self.target_country,
            "executive_target_audience": json.dumps(self.executive_target_audience),
            "proposed_title": self.proposed_title,
            "seo_strategy": json.dumps(self.seo_strategy),
            "aeo_geo_strategy": json.dumps(self.aeo_geo_strategy),
            "content_outline": json.dumps(self.content_outline),
            "faq_structures": json.dumps(self.faq_structures),
            "call_to_action": json.dumps(self.call_to_action),
            "created_at": self.created_at
        }


class ContentBlueprintDatabase:
    def __init__(self, db_path: str = "market_signals.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_blueprints (
                    blueprint_id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    target_country TEXT NOT NULL,
                    executive_target_audience TEXT NOT NULL,
                    proposed_title TEXT NOT NULL,
                    seo_strategy TEXT NOT NULL,
                    aeo_geo_strategy TEXT NOT NULL,
                    content_outline TEXT NOT NULL,
                    faq_structures TEXT NOT NULL,
                    call_to_action TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bp_industry ON content_blueprints(industry);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bp_country ON content_blueprints(target_country);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bp_opp ON content_blueprints(opportunity_id);")
            conn.commit()

    def load_top_opportunities(self, industry: Optional[str] = None, limit: int = 5) -> pd.DataFrame:
        with self._get_connection() as conn:
            query = "SELECT * FROM market_opportunities"
            params = []
            if industry:
                query += " WHERE industry = ?"
                params.append(industry)
            query += " ORDER BY opportunity_score DESC LIMIT ?"
            params.append(limit)
            return pd.read_sql_query(query, conn, params=params)

    def save_blueprints(self, blueprints: List[ContentBlueprint]) -> int:
        if not blueprints:
            return 0

        saved_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for bp in blueprints:
                d = bp.to_dict()
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO content_blueprints (
                            blueprint_id, opportunity_id, industry, keyword,
                            target_country, executive_target_audience, proposed_title,
                            seo_strategy, aeo_geo_strategy, content_outline,
                            faq_structures, call_to_action, created_at
                        ) VALUES (
                            :blueprint_id, :opportunity_id, :industry, :keyword,
                            :target_country, :executive_target_audience, :proposed_title,
                            :seo_strategy, :aeo_geo_strategy, :content_outline,
                            :faq_structures, :call_to_action, :created_at
                        )
                    """, d)
                    if cursor.rowcount > 0:
                        saved_count += 1
                except sqlite3.Error as e:
                    print(f"Database error: {e}", file=sys.stderr)
            conn.commit()
        return saved_count

    def load_blueprint_dataframe(self) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM content_blueprints ORDER BY created_at DESC", conn)


class GeminiContentEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = None

        if HAS_GENAI_SDK and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")

    def generate_blueprint(
        self,
        opp_row: Dict[str, Any]
    ) -> ContentBlueprint:
        if self.client:
            try:
                bp = self._call_gemini_content(opp_row)
                if bp:
                    return bp
            except Exception as e:
                print(f"Gemini API call failed: {e}. Using rule-based fallback.")

        return self._generate_fallback_blueprint(opp_row)

    def _call_gemini_content(self, opp: Dict[str, Any]) -> ContentBlueprint:
        prompt = f"""
You are a Senior B2B Content Strategist and Search Optimization Specialist.

Context:
- Industry: {opp['industry']}
- Keyword: {opp['keyword']}
- Target Country: {opp['target_country']}
- Opportunity Score: {opp['opportunity_score']}/100
- Commercial Intent: {opp['commercial_intent']}
- Rationale: {opp['why_now_rationale']}
- Title: {opp['recommended_report_title']}

Task:
Generate an executive content blueprint for senior decision-makers (CEOs, CTOs, Procurement Heads, VPs of R&D).
Optimize for search engine discovery and AI zero-click answers.

Return valid JSON:
{{
  "proposed_title": "{opp['recommended_report_title']}",
  "executive_target_audience": ["CEO", "CTO", "Procurement Head", "VP of R&D"],
  "seo_strategy": {{
    "meta_description": "string",
    "primary_keywords": ["string"],
    "secondary_keywords": ["string"],
    "url_slug": "string"
  }},
  "aeo_geo_strategy": {{
    "direct_answer_snippet": "string",
    "citable_facts": ["string"],
    "ai_engine_keywords": ["string"],
    "entity_tags": ["string"]
  }},
  "content_outline": [
    {{
      "header": "string",
      "key_takeaways": ["string"],
      "executive_summary": "string"
    }}
  ],
  "faq_structures": [
    {{
      "question": "string",
      "optimized_answer": "string"
    }}
  ],
  "call_to_action": {{
    "cta_headline": "string",
    "cta_button_text": "string",
    "cta_type": "string"
  }}
}}
"""

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )

        parsed = json.loads(response.text)

        return ContentBlueprint(
            blueprint_id=f"bp_{uuid.uuid4().hex[:12]}",
            opportunity_id=str(opp.get("opportunity_id", f"opp_{uuid.uuid4().hex[:8]}")),
            industry=opp["industry"],
            keyword=opp["keyword"],
            target_country=opp["target_country"],
            executive_target_audience=parsed.get("executive_target_audience", ["CEO", "CTO", "Procurement Head", "VP R&D"]),
            proposed_title=parsed.get("proposed_title", opp["recommended_report_title"]),
            seo_strategy=parsed.get("seo_strategy", {}),
            aeo_geo_strategy=parsed.get("aeo_geo_strategy", {}),
            content_outline=parsed.get("content_outline", []),
            faq_structures=parsed.get("faq_structures", []),
            call_to_action=parsed.get("call_to_action", {})
        )

    def _generate_fallback_blueprint(self, opp: Dict[str, Any]) -> ContentBlueprint:
        kw = opp["keyword"]
        country = opp["target_country"]
        ind = opp["industry"]

        seo = {
            "meta_description": f"B2B market intelligence and procurement forecast for {kw} in {country}. Explore regulatory updates, supplier capacity, and market trends.",
            "primary_keywords": [kw, f"{kw} {country}", f"B2B {kw} procurement", f"{ind} trends"],
            "secondary_keywords": [f"market size {kw}", f"supplier lead times {kw}", f"regulatory compliance {country}"],
            "url_slug": f"{kw.lower().replace(' ', '-').replace('&', 'and')}-{country.lower()}-b2b-report"
        }

        aeo_geo = {
            "direct_answer_snippet": f"In {country}, B2B procurement demand for {kw} is experiencing accelerated growth driven by regulatory updates and commercial intent. Enterprise buyers prioritize verified technical dossiers and sustainable supply chain guarantees.",
            "citable_facts": [
                f"Year-over-year B2B search momentum for {kw} in {country} increased significantly.",
                f"Regional health authorities in {country} issued updated compliance frameworks targeting commercial purity.",
                "Venture capital investments in active ingredient formulations reached record highs."
            ],
            "ai_engine_keywords": [kw, country, "B2B Procurement", "Supply Chain", "Purity Dossier", "Market Intelligence"],
            "entity_tags": ["Health Authority", "B2B Procurement", "Bio-Synthesis", "Purity Dossier", "Market Size"]
        }

        outline = [
            {
                "header": "Executive Summary & Market Drivers",
                "key_takeaways": [
                    f"Immediate procurement demand surge for {kw} in {country}.",
                    "Regulatory compliance shifts requiring formulation audits.",
                    "Strategic advantage for early supply contract commitments."
                ],
                "executive_summary": f"High-level overview detailing macro demand drivers for {kw} across {country}. Key focus rests on commercial adoption, pricing trends, and risk mitigation."
            },
            {
                "header": "Regulatory Framework & Compliance Playbook",
                "key_takeaways": [
                    "Updated dossier submission standards mandated by regional bodies.",
                    "Purity threshold and safety dossier requirements for commercial scaling."
                ],
                "executive_summary": f"Detailed analysis of regulatory requirements in {country} for {ind}, outlining safety certifications and labeling standards."
            },
            {
                "header": "Supplier Landscape & Capacity Analysis",
                "key_takeaways": [
                    "Key regional manufacturers expanding production plants.",
                    "Benchmarking ingredient purity levels and delivery timelines."
                ],
                "executive_summary": f"Mapping of primary B2B suppliers, manufacturing capacities, and supply chain logistics for {kw}."
            }
        ]

        faqs = [
            {
                "question": f"What are the regulatory requirements for importing {kw} into {country}?",
                "optimized_answer": f"Importing {kw} into {country} requires compliance with local health authority safety dossiers and verified purity certificates."
            },
            {
                "question": f"What is the projected market growth and procurement intent for {kw}?",
                "optimized_answer": f"B2B procurement search momentum for {kw} has grown significantly in {country}, driven by buyer demand and new product releases."
            }
        ]

        cta = {
            "cta_headline": f"Accelerate Your {kw} Procurement Strategy",
            "cta_button_text": "Request B2B Technical Dossier",
            "cta_type": "High-Intent Lead Magnet"
        }

        return ContentBlueprint(
            blueprint_id=f"bp_{uuid.uuid4().hex[:12]}",
            opportunity_id=str(opp.get("opportunity_id", f"opp_{uuid.uuid4().hex[:8]}")),
            industry=ind,
            keyword=kw,
            target_country=country,
            executive_target_audience=["CEO", "CTO", "Head of Procurement", "VP of R&D"],
            proposed_title=opp.get("recommended_report_title", f"Strategic B2B Market Report: {kw} in {country}"),
            seo_strategy=seo,
            aeo_geo_strategy=aeo_geo,
            content_outline=outline,
            faq_structures=faqs,
            call_to_action=cta
        )


class Module3ContentEngine:
    def __init__(self, db_path: str = "market_signals.db"):
        self.db = ContentBlueprintDatabase(db_path=db_path)
        self.content_engine = GeminiContentEngine()

    def run_content_pipeline(self, industry: Optional[str] = None, top_count: int = 5) -> Dict[str, Any]:
        df_opps = self.db.load_top_opportunities(industry=industry, limit=top_count)

        if df_opps.empty:
            return {"status": "no_opportunities", "blueprints": []}

        blueprints: List[ContentBlueprint] = []
        for idx, row in df_opps.iterrows():
            opp_dict = row.to_dict()
            bp = self.content_engine.generate_blueprint(opp_dict)
            blueprints.append(bp)

        saved_count = self.db.save_blueprints(blueprints)
        df_bp = self.db.load_blueprint_dataframe()

        return {
            "total_blueprints": len(blueprints),
            "saved_count": saved_count,
            "dataframe": df_bp
        }


def main():
    pipeline = Module3ContentEngine()
    res = pipeline.run_content_pipeline(top_count=5)
    print(f"Generated {res.get('total_blueprints', 0)} blueprints.")


if __name__ == "__main__":
    main()
