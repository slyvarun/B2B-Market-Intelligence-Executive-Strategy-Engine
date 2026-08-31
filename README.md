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

## 🚀 Streamlit Cloud Deployment Guide

This application is fully prepared for instant deployment on **Streamlit Community Cloud**, **Docker**, and Cloud hosting services (Render, Hugging Face, AWS/GCP).

---

### ☁️ Option 1: Deploy on Streamlit Community Cloud (Recommended)

1. **Push your code to GitHub**:
   Ensure your repository is pushed to a public or private GitHub repository.

2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
   - Click **"New App"**.

3. **Configure App Settings**:
   - **Repository**: `your-username/your-repo-name`
   - **Branch**: `main` (or `master`)
   - **Main file path**: `app.py` (or `datam_intelligence_poc/app.py`)

4. **Configure Secrets (API Keys)**:
   - Click **"Advanced settings..."** or go to **App Settings > Secrets** in the Streamlit Cloud dashboard.
   - Paste your API keys in TOML format (refer to `.streamlit/secrets.toml.template`):
     ```toml
     NEWS_DATA_API_KEY = "your_newsdata_api_key"
     NEWS_API_KEY = "your_newsapi_key"
     GEMINI_API_KEY = "your_gemini_api_key"
     GEMINI_MODEL = "gemini-3.7-flash"
     ```

5. **Deploy**:
   - Click **"Deploy!"**. Streamlit Cloud will install dependencies from `requirements.txt` and launch `app.py`.
   - The application automatically initializes the SQLite database schema and pre-populates demo market data on first startup!

---

### 🐳 Option 2: Run with Docker Container

1. **Build Docker Image**:
   ```bash
   docker build -t b2b-market-intelligence .
   ```

2. **Run Container**:
   ```bash
   docker run -d -p 8501:8501 --env-file .env --name b2b-app b2b-market-intelligence
   ```

3. **Access Dashboard**:
   Open browser at `http://localhost:8501`

---

### 🌐 Option 3: Deploy on Render / Heroku

- **Procfile** is included in the project root:
  ```
  web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  ```
- Set environment variables (`GEMINI_API_KEY`, `NEWS_DATA_API_KEY`, `NEWS_API_KEY`) in your Render/Heroku dashboard.

---

## Environment Setup & API Keys

Create a `.env` file locally or set secrets in Streamlit Cloud:

```env
# Live Market News APIs
NEWS_DATA_API_KEY=your_newsdata_io_key
NEWS_API_KEY=your_newsapi_org_key

# Gemini LLM API Key
GEMINI_API_KEY=your_gemini_api_key
```

