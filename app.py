import os
import sys
import json
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from module1_data_collector import MarketSignalIngestor
from module2_scoring_engine import MarketDiscoveryEngine
from module3_content_engine import Module3ContentEngine
from module4_feedback_engine import ClosedLoopFeedbackPipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "market_signals.db")


def sync_streamlit_secrets():
    """Bridge Streamlit Cloud secrets to environment variables if present."""
    try:
        if hasattr(st, "secrets") and st.secrets:
            for key, val in st.secrets.items():
                if isinstance(val, (str, int, float, bool)):
                    os.environ[str(key).upper()] = str(val)
                elif isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        os.environ[f"{key}_{sub_key}".upper()] = str(sub_val)
    except Exception:
        pass


sync_streamlit_secrets()


def get_db_connection():
    return sqlite3.connect(DB_PATH)

def check_table_exists(table_name: str) -> bool:
    if not os.path.exists(DB_PATH):
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cursor.fetchone() is not None
    except Exception:
        return False

def load_data_from_table(query: str, params: tuple = ()) -> pd.DataFrame:
    try:
        with get_db_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return pd.DataFrame()


def ensure_database_initialized():
    """Ensure database schema exists and initial demo data is loaded if missing."""
    if not os.path.exists(DB_PATH) or not check_table_exists("market_signals"):
        try:
            demo_industry = "Solar Panels"
            target_countries = ["USA", "Japan", "South Korea", "Germany", "France", "UK"]
            ingestor = MarketSignalIngestor(db_path=DB_PATH)
            ingestor.collect_and_store(industry=demo_industry, target_countries=target_countries, lookback_days=60, use_mock_fallback=True)
            
            discovery = MarketDiscoveryEngine(db_path=DB_PATH)
            discovery.run_discovery_pipeline(industry=demo_industry, target_countries=target_countries)
            
            content_engine = Module3ContentEngine(db_path=DB_PATH)
            content_engine.run_content_pipeline(industry=demo_industry, top_count=5)
            
            feedback_engine = ClosedLoopFeedbackPipeline(db_path=DB_PATH)
            feedback_engine.run_feedback_pipeline(industry=demo_industry)
        except Exception as e:
            st.error(f"Error auto-initializing demo database: {e}")


ensure_database_initialized()



st.set_page_config(
    page_title="B2B Market Intelligence & Strategy Engine",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    p, span, label, div, h1, h2, h3, h4, h5, h6, li, button {
        color: #1E293B !important;
    }
    
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #334155 !important;
        font-weight: 500;
        margin-bottom: 1.8rem;
    }
    
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #CBD5E1;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569 !important;
        background-color: transparent;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        border-bottom: 3px solid #2563EB !important;
        font-weight: 700;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #1E293B !important;
    }
    
    .streamlit-expanderHeader, div[data-testid="stExpander"] summary * {
        font-weight: 700 !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }

    code, pre, .stCodeBlock * {
        color: #0F172A !important;
        background-color: #F1F5F9 !important;
    }
    blockquote, blockquote p, blockquote * {
        color: #334155 !important;
        border-left: 4px solid #2563EB !important;
        background-color: #F8FAFC !important;
        padding: 8px 12px !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] label * {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] button * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] button:hover, section[data-testid="stSidebar"] button:hover * {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #2563EB !important;
    }

    header[data-testid="stHeader"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
    }
    header[data-testid="stHeader"] * {
        color: #FFFFFF !important;
    }

    div[data-testid="stTextInput"] input {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input *,
    div[data-testid="stInputHelp"], 
    div[data-testid="stInputHelp"] *, 
    div[data-testid="stWidgetInstructions"], 
    div[data-testid="stWidgetInstructions"] *, 
    small, 
    small * {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    div[data-testid="stMultiSelect"] *, div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    div[data-baseweb="tag"] {
        background-color: #2563EB !important;
    }
    div[data-baseweb="tag"] * {
        color: #FFFFFF !important;
    }
    div[data-testid="stSlider"] * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="main-header">🌐 B2B Market Intelligence & Executive Strategy Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Market Signals, Opportunity Scoring, Executive Content Strategy, & Business ROI Analytics</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Analysis Settings")

industry_input = st.sidebar.text_input(
    "Target Industry",
    value="Solar Panels",
    placeholder="e.g. Solar Panels, Electric Vehicles...",
    help="Enter any industry to analyze market signals and commercial opportunities."
)

target_countries = st.sidebar.multiselect(
    "Target Markets (Countries)",
    options=["USA", "Japan", "South Korea", "Germany", "France", "UK"],
    default=["USA", "Japan", "South Korea", "Germany", "France", "UK"],
    help="Select target geographical regions."
)

lookback_days = st.sidebar.slider(
    "Lookback Period (Days)",
    min_value=30,
    max_value=90,
    value=60,
    step=5
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Analysis Execution")

if st.sidebar.button("1. Collect Market Signals", width="stretch"):
    if not industry_input.strip():
        st.sidebar.warning("⚠️ Please enter a Target Industry above before running!")
    else:
        with st.spinner(f"Ingesting market signals for '{industry_input}'..."):
            ingestor = MarketSignalIngestor(db_path=DB_PATH)
            res = ingestor.collect_and_store(
                industry=industry_input.strip(),
                target_countries=target_countries,
                lookback_days=lookback_days,
                use_mock_fallback=True
            )
            st.sidebar.success(f"Collected {res['total_collected']} market signals!")
            st.rerun()

if st.sidebar.button("2. Score Market Opportunities", width="stretch"):
    if not industry_input.strip():
        st.sidebar.warning("⚠️ Please enter a Target Industry above before running!")
    else:
        with st.spinner(f"Evaluating and scoring opportunities for '{industry_input}'..."):
            discovery = MarketDiscoveryEngine(db_path=DB_PATH)
            res = discovery.run_discovery_pipeline(
                industry=industry_input.strip(),
                target_countries=target_countries
            )
            if res.get("status") == "no_signals":
                st.sidebar.warning("No market signals found! Please run 'Collect Market Signals' first.")
            else:
                st.sidebar.success(f"Scored {res['opportunities_discovered']} market opportunities!")
                st.rerun()

if st.sidebar.button("3. Generate Content Strategy", width="stretch"):
    if not industry_input.strip():
        st.sidebar.warning("⚠️ Please enter a Target Industry above before running!")
    else:
        with st.spinner(f"Generating C-suite executive content strategy for '{industry_input}'..."):
            content_engine = Module3ContentEngine(db_path=DB_PATH)
            res = content_engine.run_content_pipeline(industry=industry_input.strip(), top_count=5)
            if res.get("status") == "no_opportunities":
                st.sidebar.warning("No opportunities found! Please run 'Score Market Opportunities' first.")
            else:
                st.sidebar.success(f"Generated {res['total_blueprints']} content blueprints!")
                st.rerun()

if st.sidebar.button("4. Analyze Business Performance", width="stretch"):
    if not industry_input.strip():
        st.sidebar.warning("⚠️ Please enter a Target Industry above before running!")
    else:
        with st.spinner(f"Analyzing conversion performance for '{industry_input}'..."):
            feedback_engine = ClosedLoopFeedbackPipeline(db_path=DB_PATH)
            res = feedback_engine.run_feedback_pipeline(industry=industry_input.strip())
            if res.get("status") == "no_opportunities":
                st.sidebar.warning("No opportunities found! Please run 'Score Market Opportunities' first.")
            else:
                st.sidebar.success("Business performance analytics updated!")
                st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🚀 Run Full Market Analysis", width="stretch", type="primary"):
    if not industry_input.strip():
        st.sidebar.warning("⚠️ Please enter a Target Industry above before running!")
    else:
        with st.spinner(f"Executing complete market analysis for '{industry_input}'..."):
            ingestor = MarketSignalIngestor(db_path=DB_PATH)
            ingestor.collect_and_store(industry=industry_input.strip(), target_countries=target_countries, lookback_days=lookback_days)
            
            discovery = MarketDiscoveryEngine(db_path=DB_PATH)
            discovery.run_discovery_pipeline(industry=industry_input.strip(), target_countries=target_countries)
            
            content_engine = Module3ContentEngine(db_path=DB_PATH)
            content_engine.run_content_pipeline(industry=industry_input.strip(), top_count=5)
            
            feedback_engine = ClosedLoopFeedbackPipeline(db_path=DB_PATH)
            feedback_engine.run_feedback_pipeline(industry=industry_input.strip())
            
            st.sidebar.success("🎉 Complete market analysis executed successfully!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Data Management")
if st.sidebar.button("🔄 Reset & Re-seed Demo Data", width="stretch"):
    with st.spinner("Resetting and re-seeding demo database..."):
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        ensure_database_initialized()
        st.sidebar.success("Database re-seeded with demo data!")
        st.rerun()



tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Market Signals",
    "⚡ Opportunity Matrix",
    "📝 Executive Content Strategy",
    "📊 Business ROI & Performance"
])

with tab1:
    st.subheader(f"📡 Ingested Market Signals {f'— {industry_input}' if industry_input.strip() else ''}")

    if not industry_input.strip():
        st.info("👈 **Please enter a Target Industry in the sidebar** (e.g. *Solar Panels*, *Electric Vehicles*) and click **'1. Collect Market Signals'** or **'🚀 Run Full Market Analysis'** to begin.")
    elif not check_table_exists("market_signals"):
        st.info("ℹ️ No market signals available. Click **'1. Collect Market Signals'** in the sidebar to begin analysis.")
    else:
        df_signals = load_data_from_table("SELECT * FROM market_signals WHERE industry = ? ORDER BY date DESC", params=(industry_input.strip(),))
        
        if df_signals.empty:
            st.warning(f"⚠️ No market signals found for **'{industry_input}'**. Click **'1. Collect Market Signals'** in the sidebar to analyze this industry.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Signals Detected", len(df_signals))
            with col2:
                st.metric("Active Target Markets", df_signals["country"].nunique())
            with col3:
                st.metric("Signal Categories", df_signals["signal_type"].nunique())
            with col4:
                avg_metric = round(df_signals["quantitative_metric"].mean(), 1)
                st.metric("Avg Signal Intensity", f"{avg_metric} / 100")

            st.markdown("---")

            c1, c2 = st.columns(2)
            with c1:
                st.write("**Signal Volume by Target Market**")
                country_counts = df_signals["country"].value_counts()
                st.bar_chart(country_counts)
            with c2:
                st.write("**Signal Volume by Category**")
                type_counts = df_signals["signal_type"].value_counts()
                st.bar_chart(type_counts)

            st.markdown("---")
            st.write(f"**Market Signals Detail Table for '{industry_input}'**")
            display_cols = ["signal_id", "industry", "country", "signal_type", "title", "source", "date", "quantitative_metric"]
            st.dataframe(df_signals[display_cols], width="stretch")


with tab2:
    st.subheader(f"⚡ Market Opportunity Matrix {f'— {industry_input}' if industry_input.strip() else ''}")

    if not industry_input.strip():
        st.info("👈 **Please enter a Target Industry in the sidebar** and click **'2. Score Market Opportunities'** to evaluate signals.")
    elif not check_table_exists("market_opportunities"):
        st.info("ℹ️ No market opportunities scored yet. Click **'2. Score Market Opportunities'** in the sidebar to evaluate signals.")
    else:
        df_opps = load_data_from_table("SELECT * FROM market_opportunities WHERE industry = ? ORDER BY opportunity_score DESC", params=(industry_input.strip(),))
        
        if df_opps.empty:
            st.warning(f"⚠️ No opportunities scored yet for **'{industry_input}'**. Click **'2. Score Market Opportunities'** in the sidebar.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Discovered Opportunities", len(df_opps))
            with m2:
                max_score = df_opps["opportunity_score"].max()
                st.metric("Top Opportunity Score", f"{max_score:.1f}")
            with m3:
                high_intent_count = (df_opps["commercial_intent"] == "High").sum()
                st.metric("High Commercial Intent", high_intent_count)
            with m4:
                avg_opp_score = round(df_opps["opportunity_score"].mean(), 1)
                st.metric("Average Score", f"{avg_opp_score}")

            st.markdown("---")
            st.subheader(f"🎯 Top Opportunities & Why-Now Rationales for '{industry_input}'")

            top_3 = df_opps.head(3)
            for idx, row in top_3.iterrows():
                with st.expander(f"⭐ **#{idx+1}: {row['keyword']}** ({row['target_country']}) — Score: {row['opportunity_score']}/100", expanded=True):
                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        st.markdown(f"**Target Region**: {row['target_country']}")
                        st.markdown(f"**Commercial Intent**: `{row['commercial_intent']}`")
                        st.markdown(f"**Recommended Report Title**:\n*{row['recommended_report_title']}*")
                    with col_b:
                        st.markdown(f"**Why-Now Rationale**:\n> {row['why_now_rationale']}")

            st.markdown("---")
            st.write(f"**Full Opportunity Discovery Matrix**")
            st.dataframe(
                df_opps[["opportunity_score", "keyword", "target_country", "commercial_intent", "recommended_report_title", "why_now_rationale"]],
                width="stretch"
            )


with tab3:
    st.subheader(f"📝 Executive Content Strategy & Search Blueprint {f'— {industry_input}' if industry_input.strip() else ''}")

    if not industry_input.strip():
        st.info("👈 **Please enter a Target Industry in the sidebar** and click **'3. Generate Content Strategy'** to create executive strategy plans.")
    elif not check_table_exists("content_blueprints"):
        st.info("ℹ️ No content blueprints generated yet. Click **'3. Generate Content Strategy'** in the sidebar to create executive strategy plans.")
    else:
        df_bp = load_data_from_table("SELECT * FROM content_blueprints WHERE industry = ? ORDER BY created_at DESC", params=(industry_input.strip(),))
        
        if df_bp.empty:
            st.warning(f"⚠️ No strategy blueprints generated yet for **'{industry_input}'**. Click **'3. Generate Content Strategy'** in the sidebar.")
        else:
            blueprint_options = [f"{row['keyword']} ({row['target_country']}) — {row['proposed_title']}" for _, row in df_bp.iterrows()]
            selected_option = st.selectbox("🔍 Select Opportunity Blueprint to Inspect", options=blueprint_options)

            selected_idx = blueprint_options.index(selected_option)
            selected_row = df_bp.iloc[selected_idx]

            seo = json.loads(selected_row["seo_strategy"]) if isinstance(selected_row["seo_strategy"], str) else selected_row["seo_strategy"]
            aeo = json.loads(selected_row["aeo_geo_strategy"]) if isinstance(selected_row["aeo_geo_strategy"], str) else selected_row["aeo_geo_strategy"]
            outline = json.loads(selected_row["content_outline"]) if isinstance(selected_row["content_outline"], str) else selected_row["content_outline"]
            faqs = json.loads(selected_row["faq_structures"]) if isinstance(selected_row["faq_structures"], str) else selected_row["faq_structures"]
            cta = json.loads(selected_row["call_to_action"]) if isinstance(selected_row["call_to_action"], str) else selected_row["call_to_action"]
            audiences = json.loads(selected_row["executive_target_audience"]) if isinstance(selected_row["executive_target_audience"], str) else selected_row["executive_target_audience"]

            st.markdown(f"### 📑 Title: {selected_row['proposed_title']}")
            st.markdown(f"**Target Executive Audience**: `{', '.join(audiences)}` | **Target Market**: `{selected_row['target_country']}`")

            col_x, col_y = st.columns(2)

            with col_x:
                st.markdown("#### 🔍 Search Engine Positioning Strategy")
                st.markdown(f"**Meta Description**:\n*{seo.get('meta_description', '')}*")
                st.markdown(f"**Primary Focus Keywords**: `{', '.join(seo.get('primary_keywords', []))}`")
                st.markdown(f"**Secondary Keywords**: `{', '.join(seo.get('secondary_keywords', []))}`")
                st.markdown(f"**URL Slug**: `/{seo.get('url_slug', '')}`")

            with col_y:
                st.markdown("#### 🤖 AI Answer Engine & Zero-Click Positioning")
                st.markdown(f"**Direct Executive Answer Snippet**:\n> {aeo.get('direct_answer_snippet', '')}")
                st.markdown(f"**Entity Tags**: `{', '.join(aeo.get('entity_tags', []))}`")
                st.markdown("**Citable Industry Facts**:")
                for fact in aeo.get("citable_facts", []):
                    st.markdown(f"- {fact}")

            st.markdown("---")
            st.markdown("#### 📋 Executive Content Outline")
            for sec in outline:
                st.markdown(f"##### 📌 {sec.get('header', '')}")
                st.markdown(sec.get("executive_summary", ""))
                st.markdown("**Key Takeaways**:")
                for kw_item in sec.get("key_takeaways", []):
                    st.markdown(f"  - {kw_item}")

            st.markdown("---")
            c_faq, c_cta = st.columns(2)
            with c_faq:
                st.markdown("#### ❓ Executive Q&A FAQs")
                for item in faqs:
                    st.markdown(f"**Q: {item.get('question')}**")
                    st.markdown(f"A: {item.get('optimized_answer')}\n")

            with c_cta:
                st.markdown("#### 🎯 Lead Generation Call To Action")
                st.info(f"**{cta.get('cta_headline', '')}**\n\nButton Label: `[{cta.get('cta_button_text', '')}]`\n\nStrategy Type: *{cta.get('cta_type', '')}*")


with tab4:
    st.subheader(f"📊 Business ROI & Performance Analytics {f'— {industry_input}' if industry_input.strip() else ''}")

    if not industry_input.strip():
        st.info("👈 **Please enter a Target Industry in the sidebar** and click **'4. Analyze Business Performance'** to view analytics.")
    elif not check_table_exists("feedback_analytics"):
        st.info("ℹ️ No performance analytics recorded yet. Click **'4. Analyze Business Performance'** in the sidebar to generate ROI metrics.")
    else:
        df_fb = load_data_from_table(
            "SELECT * FROM feedback_analytics WHERE opportunity_id IN (SELECT opportunity_id FROM market_opportunities WHERE industry = ?) ORDER BY roi_score DESC",
            params=(industry_input.strip(),)
        )
        
        if df_fb.empty:
            st.warning(f"⚠️ No analytics recorded yet for **'{industry_input}'**. Click **'4. Analyze Business Performance'** in the sidebar.")
        else:
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                total_leads = df_fb["qualified_b2b_leads"].sum()
                st.metric("Total Qualified B2B Leads", f"{total_leads:,}")
            with k2:
                total_rev = df_fb["report_sales_revenue"].sum()
                st.metric("Report Sales Revenue", f"${total_rev:,.2f}")
            with k3:
                avg_conv = round(df_fb["conversion_rate"].mean(), 2)
                st.metric("Avg Conversion Rate", f"{avg_conv}%")
            with k4:
                avg_roi = round(df_fb["roi_score"].mean(), 1)
                st.metric("Avg Business ROI Score", f"{avg_roi} / 100")

            st.markdown("---")
            st.subheader(f"📈 Performance Matrix for '{industry_input}': Opportunity Score vs Revenue")

            display_fb = df_fb[[
                "keyword", "target_country", "initial_opportunity_score",
                "organic_traffic", "qualified_b2b_leads", "report_sales_revenue", "roi_score"
            ]].copy()
            
            display_fb["report_sales_revenue"] = display_fb["report_sales_revenue"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_fb, width="stretch")

            st.markdown("---")
            st.subheader("🤖 Algorithm Scoring Weight Adjustments")

            if check_table_exists("algorithm_weights"):
                df_weights = load_data_from_table("SELECT * FROM algorithm_weights ORDER BY version DESC LIMIT 1")
                if not df_weights.empty:
                    latest = df_weights.iloc[0]
                    sig_weights = json.loads(latest["signal_weights"])
                    cntry_boosts = json.loads(latest["country_boost_factors"])

                    w_col1, w_col2 = st.columns(2)
                    with w_col1:
                        st.write(f"**Signal Factor Weighting (Version v{latest['version']})**")
                        df_sig_w = pd.DataFrame([
                            {"Signal Factor": k.replace("_", " ").title(), "Weight %": f"{v*100:.1f}%"}
                            for k, v in sig_weights.items()
                        ])
                        st.table(df_sig_w)

                    with w_col2:
                        st.write(f"**Country Market Boost Factors**")
                        df_cntry_b = pd.DataFrame([
                            {"Country": k, "Boost Multiplier": f"{v:.2f}x"}
                            for k, v in cntry_boosts.items()
                        ])
                        st.table(df_cntry_b)

st.markdown("---")
st.caption("B2B Market Intelligence & Executive Strategy Engine • Version 1.0.0")
