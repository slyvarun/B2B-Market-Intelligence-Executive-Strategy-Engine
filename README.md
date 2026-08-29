# B2B Market Intelligence & Executive Strategy Platform

An end-to-end B2B Market Intelligence platform featuring live market signal collection, AI opportunity scoring, C-suite content strategy generation, closed-loop ROI performance analytics, and an executive **Streamlit visual dashboard (`app.py`)**.

---

## 🎨 Streamlit Visual Dashboard (`app.py`)

Run the full interactive Web Application UI with a single command:

```bash
streamlit run app.py
```

### Dashboard Tabs & UI Features:
- **📡 Market Signals**: Displays ingested market signals, signal intensity metrics, active target regions, signal categories, and signal breakdown charts.
- **⚡ Opportunity Matrix**: Displays ranked market opportunities scored by Gemini 3.6 Flash, highlighting top opportunity Why-Now rationales and commercial procurement intent.
- **📝 Executive Content Strategy**: Interactive blueprint inspector displaying search engine positioning, AI zero-click answer snippets, C-suite outlines, Q&A FAQs, and lead generation CTAs.
- **📊 Business ROI & Performance**: High-level KPI cards (sales revenue, qualified leads, ROI score), performance matrix table, and adaptive scoring weight adjustments.
- **⚙️ Sidebar Controls**: Dynamic industry text input, target market multi-select, lookback slider, and one-click execution triggers.

---

## System Architecture

```
[Market Signal Collector] ──> [Opportunity Scoring Engine] ──> [Executive Content Strategy] ──> [Business ROI Feedback]
  (NewsData & NewsAPI)            (Gemini 3.6 Flash)            (Search & AI Positioning)          (Closed-Loop Learning)
           │                               │                               │                               │
           ▼                               ▼                               ▼                               ▼
 `market_signals` table         `market_opportunities` table      `content_blueprints` table        `feedback_analytics` &
   in market_signals.db           in market_signals.db               in market_signals.db          `algorithm_weights` tables
```

---

## Pipeline Execution

### 1. Master Pipeline Runner
```bash
python run_all.py
```

### 2. Market Signal Ingestion
```bash
python module1_data_collector.py
```

### 3. Opportunity Scoring Engine
```bash
python module2_scoring_engine.py
```

### 4. Content Strategy Engine
```bash
python module3_content_engine.py
```

### 5. Business ROI & Performance Analytics
```bash
python module4_feedback_engine.py
```

---

## Environment Setup & API Keys

Create a `.env` file in the project folder:

```env
# Live Market News APIs
NEWS_DATA_API_KEY=your_newsdata_io_key
NEWS_API_KEY=your_newsapi_org_key

# Gemini LLM API Key
GEMINI_API_KEY=your_gemini_api_key
```
