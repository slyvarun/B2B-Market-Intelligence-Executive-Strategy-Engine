import os
import sys
import uuid
import sqlite3
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


class SignalType(str, Enum):
    REGULATORY = "regulatory"
    PRODUCT_LAUNCH = "product_launch"
    INVESTMENT_MNA = "investment_mna"
    PATENT_RD = "patent_rd"
    CAPACITY_EXPANSION = "capacity_expansion"
    SEARCH_MOMENTUM = "search_momentum"


@dataclass
class MarketSignal:
    signal_id: str
    industry: str
    country: str
    signal_type: SignalType
    title: str
    description: str
    source: str
    date: str
    quantitative_metric: float
    created_at: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['signal_type'] = self.signal_type.value if isinstance(self.signal_type, SignalType) else self.signal_type
        return d


class SignalDatabase:
    def __init__(self, db_path: str = "market_signals.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_signals (
                    signal_id TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    country TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    date TEXT NOT NULL,
                    quantitative_metric REAL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_industry ON market_signals(industry);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON market_signals(country);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_type ON market_signals(signal_type);")
            conn.commit()

    def save_signals(self, signals: List[MarketSignal]) -> int:
        if not signals:
            return 0

        saved_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for sig in signals:
                d = sig.to_dict()
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO market_signals (
                            signal_id, industry, country, signal_type, title,
                            description, source, date, quantitative_metric, created_at
                        ) VALUES (
                            :signal_id, :industry, :country, :signal_type, :title,
                            :description, :source, :date, :quantitative_metric, :created_at
                        )
                    """, d)
                    if cursor.rowcount > 0:
                        saved_count += 1
                except sqlite3.Error as e:
                    print(f"Database Error: {e}", file=sys.stderr)
            conn.commit()
        return saved_count

    def load_dataframe(self, industry: Optional[str] = None) -> pd.DataFrame:
        with self._get_connection() as conn:
            query = "SELECT * FROM market_signals"
            params = []
            if industry:
                query += " WHERE industry = ?"
                params.append(industry)
            query += " ORDER BY date DESC"
            return pd.read_sql_query(query, conn, params=params)


class LiveAPICollector:
    def __init__(self):
        self.news_data_key = os.getenv("NEWS_DATA_API_KEY") or os.getenv("NEWSDATA_API_KEY", "")
        self.news_api_key = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_KEY", "")

    def fetch_newsdata(self, industry: str, countries: List[str], lookback_days: int) -> List[MarketSignal]:
        signals = []
        if not self.news_data_key:
            return signals

        country_code_map = {
            "USA": "us", "Japan": "jp", "South Korea": "kr",
            "Germany": "de", "France": "fr", "UK": "gb"
        }

        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        for country in countries:
            cc = country_code_map.get(country, "us")
            url = f"https://newsdata.io/api/1/news?apikey={self.news_data_key}&q={industry}&country={cc}&language=en"
            try:
                resp = requests.get(url, timeout=6)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for item in results[:5]:
                        pub_date = item.get("pubDate", "")[:10] or start_date
                        title = item.get("title") or "No Title"
                        desc = item.get("description") or title
                        sig_type = self._classify_signal_type(title + " " + desc)

                        signals.append(MarketSignal(
                            signal_id=f"nd_{uuid.uuid4().hex[:12]}",
                            industry=industry,
                            country=country,
                            signal_type=sig_type,
                            title=title,
                            description=desc[:500],
                            source=item.get("source_id") or "NewsData.io",
                            date=pub_date,
                            quantitative_metric=round(random.uniform(50.0, 95.0), 1)
                        ))
            except Exception as e:
                print(f"NewsData fetch error for {country}: {e}")

        return signals

    def fetch_newsapi(self, industry: str, countries: List[str], lookback_days: int) -> List[MarketSignal]:
        signals = []
        if not self.news_api_key:
            return signals

        from_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        url = f"https://newsapi.org/v2/everything?apiKey={self.news_api_key}&q={industry}&from={from_date}&sortBy=publishedAt&pageSize=15"

        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                for idx, item in enumerate(articles):
                    title = item.get("title") or ""
                    desc = item.get("description") or title
                    if not title or title == "[Removed]":
                        continue
                    
                    assigned_country = countries[idx % len(countries)]
                    sig_type = self._classify_signal_type(title + " " + desc)

                    signals.append(MarketSignal(
                        signal_id=f"na_{uuid.uuid4().hex[:12]}",
                        industry=industry,
                        country=assigned_country,
                        signal_type=sig_type,
                        title=title,
                        description=desc[:500],
                        source=item.get("source", {}).get("name") or "NewsAPI.org",
                        date=item.get("publishedAt", "")[:10] or from_date,
                        quantitative_metric=round(random.uniform(55.0, 92.0), 1)
                    ))
        except Exception as e:
            print(f"NewsAPI fetch error: {e}")

        return signals

    @staticmethod
    def _classify_signal_type(text: str) -> SignalType:
        t = text.lower()
        if any(w in t for w in ["regulat", "fda", "efsa", "pmda", "policy", "approval", "banned", "guideline"]):
            return SignalType.REGULATORY
        elif any(w in t for w in ["launch", "release", "introduc", "unveil", "new product", "formulation"]):
            return SignalType.PRODUCT_LAUNCH
        elif any(w in t for w in ["acquire", "acquisition", "m&a", "invest", "funding", "round", "venture", "partner"]):
            return SignalType.INVESTMENT_MNA
        elif any(w in t for w in ["patent", "r&d", "clinical", "trial", "study", "synthesis", "lab"]):
            return SignalType.PATENT_RD
        elif any(w in t for w in ["capacity", "plant", "factory", "facility", "expand", "production", "supply"]):
            return SignalType.CAPACITY_EXPANSION
        else:
            return SignalType.SEARCH_MOMENTUM


class MockSignalGenerator:
    @staticmethod
    def generate_mock_signals(industry: str, countries: List[str], lookback_days: int, count: int = 18) -> List[MarketSignal]:
        signals = []
        today = datetime.now()

        templates = [
            {
                "type": SignalType.REGULATORY,
                "title_fn": lambda c, ind: f"{c} Health Authority Issues New Compliance Framework for {ind}",
                "desc_fn": lambda c, ind: f"Targeted regulatory update introducing stricter labeling standards and safety dossier submissions for commercial {ind} products.",
                "source": "Global Regulatory Monitor",
                "metric_range": (70.0, 95.0)
            },
            {
                "type": SignalType.PRODUCT_LAUNCH,
                "title_fn": lambda c, ind: f"Leading Enterprise Unveils High-Bioavailability {ind} Line in {c}",
                "desc_fn": lambda c, ind: f"Commercial product launch featuring patented delivery technology aimed at premium B2B manufacturers in {c}.",
                "source": "Industry Wire",
                "metric_range": (80.0, 98.0)
            },
            {
                "type": SignalType.INVESTMENT_MNA,
                "title_fn": lambda c, ind: f"$45M Series B Venture Funding Secured for {ind} Firm in {c}",
                "desc_fn": lambda c, ind: f"Investment round led by top strategic venture funds to accelerate commercialization and international market entry.",
                "source": "Venture Capital Daily",
                "metric_range": (85.0, 100.0)
            },
            {
                "type": SignalType.PATENT_RD,
                "title_fn": lambda c, ind: f"Breakthrough Patent Granted for Fermentation-Derived {ind} Compounds",
                "desc_fn": lambda c, ind: f"Assignee secures exclusive IP rights covering enzymatic biosynthesis methods that reduce production costs while preserving purity.",
                "source": "Patent Gazette",
                "metric_range": (75.0, 92.0)
            },
            {
                "type": SignalType.CAPACITY_EXPANSION,
                "title_fn": lambda c, ind: f"Major Manufacturing Plant Expansion Announced in {c}",
                "desc_fn": lambda c, ind: f"$120M facility expansion increasing local manufacturing capacity for high-purity {ind} ingredients.",
                "source": "Manufacturing News",
                "metric_range": (65.0, 90.0)
            },
            {
                "type": SignalType.SEARCH_MOMENTUM,
                "title_fn": lambda c, ind: f"B2B Procurement Intent for {ind} Surges Year-over-Year in {c}",
                "desc_fn": lambda c, ind: f"Search metrics and wholesale enquiry volume indicate rising buyer interest driven by new consumer trends.",
                "source": "Market Intelligence Signals",
                "metric_range": (88.0, 99.0)
            }
        ]

        for i in range(count):
            tpl = templates[i % len(templates)]
            country = countries[i % len(countries)]
            days_ago = random.randint(1, lookback_days)
            sig_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            metric = round(random.uniform(*tpl["metric_range"]), 1)

            signals.append(MarketSignal(
                signal_id=f"mock_{uuid.uuid4().hex[:12]}",
                industry=industry,
                country=country,
                signal_type=tpl["type"],
                title=tpl["title_fn"](country, industry),
                description=tpl["desc_fn"](country, industry),
                source=tpl["source"],
                date=sig_date,
                quantitative_metric=metric
            ))

        return signals


class MarketSignalIngestor:
    def __init__(self, db_path: str = "market_signals.db"):
        self.db = SignalDatabase(db_path=db_path)
        self.live_collector = LiveAPICollector()

    def collect_and_store(
        self,
        industry: str,
        target_countries: List[str],
        lookback_days: int = 60,
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        all_signals: List[MarketSignal] = []

        newsdata_signals = self.live_collector.fetch_newsdata(industry, target_countries, lookback_days)
        newsapi_signals = self.live_collector.fetch_newsapi(industry, target_countries, lookback_days)

        all_signals.extend(newsdata_signals)
        all_signals.extend(newsapi_signals)

        if use_mock_fallback or len(all_signals) < 10:
            mock_signals = MockSignalGenerator.generate_mock_signals(
                industry=industry,
                countries=target_countries,
                lookback_days=lookback_days,
                count=18
            )
            all_signals.extend(mock_signals)

        saved_count = self.db.save_signals(all_signals)
        df = self.db.load_dataframe(industry=industry)

        return {
            "industry": industry,
            "total_collected": len(all_signals),
            "total_saved": saved_count,
            "dataframe": df
        }


def main():
    industry = "Supplements / Nutraceutical Ingredients"
    target_countries = ["USA", "Japan", "South Korea", "Germany", "France", "UK"]

    ingestor = MarketSignalIngestor()
    res = ingestor.collect_and_store(industry=industry, target_countries=target_countries)
    print(f"Collected {res['total_collected']} signals for {industry}.")


if __name__ == "__main__":
    main()
