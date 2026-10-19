import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.engine.nlp_engine import RiskNLPEngine
from src.stress_testing.portfolio import PortfolioStressTester

st.set_page_config(
    page_title="FinRisk AI: Risk & Capital Adequacy Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 14px;
        border: 1px solid #e2e8f0;
    }
    .badge-breach {
        color: #b91c1c;
        background-color: #fee2e2;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-safe {
        color: #15803d;
        background-color: #dcfce7;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_resources():
    return RiskNLPEngine(), PortfolioStressTester()


nlp_engine, stress_tester = init_resources()

# Load feed data
try:
    with open("data/sample_feed.json", "r") as f:
        sample_feed = json.load(f)
except Exception:
    sample_feed = []

st.title("🛡️ FinRisk AI: Unified NLP Risk Engine & Portfolio Stress Platform")
st.markdown("**S&P Global & CRISIL Campus Hackathon Prototype** | Institutional Credit & Basel III Capital Stress Testing")

# Sidebar Controls
st.sidebar.header("Data Ingestion Controls")
feed_mode = st.sidebar.radio("Select Ingestion Stream:", ["Preloaded News & Social Feed", "Live Custom Entry"])

if feed_mode == "Preloaded News & Social Feed" and sample_feed:
    selected_item = st.sidebar.selectbox(
        "Choose Ingestion Record:",
        sample_feed,
        format_func=lambda x: f"[{x['source'].upper()}] {x['title'][:45]}..."
    )
    title_input = selected_item["title"]
    text_input = selected_item["text"]
    source_input = selected_item["source"]
else:
    title_input = st.sidebar.text_input("Headline", "Corporate Loan Alpha faces default watch after liquidity crunch")
    text_input = st.sidebar.text_area(
        "Article Content",
        "Lenders prepare for severe credit impairment as debt defaults mount across commercial loans. Spread widening and downgrade expected."
    )
    source_input = st.sidebar.selectbox("Source Channel", ["financial_news", "social_media"])

# Process with NLP Risk Engine
signal = nlp_engine.process_text(
    item_id="LIVE-RUN",
    title=title_input,
    text=text_input,
    source=source_input,
    timestamp="2026-10-18T21:30:00Z"
)

# Header Metric Bar
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Entity Detected", signal["extracted_entity"])
col2.metric("Event Classification", signal["event_classification"])
col3.metric("FinBERT Sentiment", f"{signal['sentiment_score']}", delta=signal["sentiment_label"])
col4.metric("Impact Severity (1-10)", f"{signal['impact_score']} / 10")
col5.metric(
    "Stress Trigger",
    "TRIGGERED" if signal["stress_test_triggered"] else "NOMINAL",
    delta_color="inverse" if signal["stress_test_triggered"] else "normal"
)

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📥 Ingested Unstructured Text")
    st.markdown(f"**Source:** `{signal['source']}` | **Entity Scope:** `{signal['extracted_entity']}`")
    st.info(f"**{title_input}**\n\n{text_input}")

    st.subheader("🔍 Explainability & Evidence Attribution")
    if signal["evidence_triggers"]:
        st.write("Identified Driver Triggers:")
        st.write(" ".join([f"`{w}`" for w in signal["evidence_triggers"]]))
    else:
        st.write("No severe keyword triggers detected.")

    st.subheader("⚙️ Machine-Readable Structured Signal (JSON)")
    st.json(signal)

with col_right:
    st.subheader("🏦 Wholesale Banking Portfolio Stress Test (Module B)")

    if signal["stress_test_triggered"]:
        results = stress_tester.run_stress_test(
            event_type=signal["event_classification"],
            impact_score=signal["impact_score"],
            detected_entity=signal["extracted_entity"]
        )

        st.warning(f"⚠️ Automated Basel III Stress Test Executed for **{signal['event_classification']}** (Severity {signal['impact_score']}/10)")

        # CRAR & Capital Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Pre-Stress Value", f"₹{results['total_initial_lakhs']} L")
        c2.metric("Post-Stress Value", f"₹{results['total_stressed_lakhs']} L")
        c3.metric("Simulated Loss", f"-₹{results['total_loss_lakhs']} L", f"-{results['portfolio_loss_pct']}%", delta_color="inverse")

        st.markdown("#### 🏛️ Regulatory Capital Adequacy (CRAR)")
        crar1, crar2, crar3 = st.columns(3)
        crar1.metric("Baseline CRAR", f"{results['pre_crar_pct']}%")
        crar2.metric("Stressed CRAR", f"{results['post_crar_pct']}%", f"{round(results['post_crar_pct'] - results['pre_crar_pct'], 2)}%", delta_color="inverse")

        with crar3:
            st.write("**Regulatory Status (11.5% Min):**")
            if results["capital_adequacy_breached"]:
                st.markdown("<span class='badge-breach'>CRAR BREACHED - CAPITAL ACTION REQUIRED</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge-safe'>BUFFER COMPLIANT</span>", unsafe_allow_html=True)

        # Asset-Level Chart
        df_chart = pd.DataFrame(results["asset_breakdown"])
        fig = go.Figure(data=[
            go.Bar(
                name="Pre-Stress Valuation (₹L)",
                x=df_chart["asset_name"],
                y=df_chart["initial_value_inr_lakhs"],
                marker_color="#2563eb"
            ),
            go.Bar(
                name="Stressed Valuation (₹L)",
                x=df_chart["asset_name"],
                y=df_chart["stressed_value_inr_lakhs"],
                marker_color="#dc2626"
            )
        ])
        fig.update_layout(
            barmode="group",
            title="Asset-Level Capital Impairment (Basel Expected Loss & Duration Repricing)",
            xaxis_tickangle=-25,
            height=340,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_chart[["asset_name", "asset_type", "initial_value_inr_lakhs", "loss_amount_inr_lakhs", "stress_mechanic"]].rename(
                columns={
                    "asset_name": "Asset",
                    "asset_type": "Type",
                    "initial_value_inr_lakhs": "Initial (₹L)",
                    "loss_amount_inr_lakhs": "Loss (₹L)",
                    "stress_mechanic": "Applied Financial Formula / Shock Rationale"
                }
            ),
            use_container_width=True
        )
    else:
        st.success("✅ Nominal Risk State: Impact score is below the critical threshold (Impact < 7 or Sentiment >= -0.2). Wholesale capital buffers remain within baseline parameters.")
        df_base = stress_tester.portfolio_df
        st.write("Current Synthetic Portfolio Base (₹100 Lakhs Total Exposure):")
        st.dataframe(df_base[["asset_id", "asset_name", "asset_type", "initial_value_inr_lakhs", "duration_years"]], use_container_width=True)