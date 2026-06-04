"""DataPulse Quality Dashboard - DE2 (Odile)

Run:
    pip install streamlit plotly pandas
    streamlit run dashboards/quality_dashboard.py
"""

import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Path setup 
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")
sys.path.insert(0, os.path.join(BASE_DIR, "pipeline"))

from analytics import (
    score_summary,
    rule_failure_rates,
    quality_trend,
    worst_datasets,
    monthly_summary,
)

# Page config
st.set_page_config(
    page_title="DataPulse Quality Dashboard",
    page_icon="📊",
    layout="wide",
)

# Header 
st.title("📊 DataPulse Data Quality Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.divider()

# Load data 
@st.cache_data(ttl=30)  # Cache for 5 minutes
def load_summary():
    return score_summary()

@st.cache_data(ttl=30)
def load_rule_failures():
    return rule_failure_rates()

@st.cache_data(ttl=30)
def load_monthly():
    return monthly_summary()

summary      = load_summary()
rule_df      = load_rule_failures()
monthly_df   = load_monthly()

# Sidebar filters 
st.sidebar.header("🔍 Filters")

all_datasets  = summary["dataset"].tolist()
selected      = st.sidebar.multiselect(
    "Select datasets",
    options=all_datasets,
    default=all_datasets,
)

score_min, score_max = st.sidebar.slider(
    "Score range",
    min_value=0,
    max_value=100,
    value=(0, 100),
)

filtered_summary = summary[
    summary["dataset"].isin(selected) &
    summary["score"].between(score_min, score_max)
]

st.sidebar.divider()
st.sidebar.caption("DataPulse · DE2 Cohort 2")

# KPI cards
st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

avg_score    = round(filtered_summary["score"].mean(), 1) if len(filtered_summary) > 0 else 0
total_rows   = filtered_summary["total_rows"].sum()
total_failed = filtered_summary["failed_rows"].sum()
best_dataset = filtered_summary.loc[filtered_summary["score"].idxmax(), "dataset"] if len(filtered_summary) > 0 else "N/A"

col1.metric("Average Score",    f"{avg_score}/100")
col2.metric("Total Rows",       f"{total_rows:,}")
col3.metric("Total Failed Rows",f"{total_failed:,}")
col4.metric("Best Dataset",     best_dataset)

st.divider()

# Row 1: Score summary + Rule failure rates 
col_left, col_right = st.columns(2)

with col_left:
    st.subheader(" Dataset Quality Scores")

    if len(filtered_summary) == 0:
        st.warning("No datasets match the current filters.")
    else:
        fig = px.bar(
            filtered_summary.sort_values("score"),
            x="score",
            y="dataset",
            orientation="h",
            color="score",
            color_continuous_scale=["#E24B4A", "#F5A623", "#27AE60"],
            range_color=[0, 100],
            text="score",
            labels={"score": "Quality Score", "dataset": "Dataset"},
        )
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            coloraxis_showscale=False,
            height=350,
            margin=dict(l=0, r=20, t=20, b=0),
        )
        fig.add_vline(x=95, line_dash="dash", line_color="green",
                      annotation_text="Target ~95")
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader(" Rule Failure Rates")

    fig2 = px.bar(
        rule_df.sort_values("failure_rate_pct", ascending=False),
        x="rule",
        y="failure_rate_pct",
        color="failure_rate_pct",
        color_continuous_scale=["#27AE60", "#F5A623", "#E24B4A"],
        text="failure_rate_pct",
        labels={"rule": "Rule Type", "failure_rate_pct": "Failure Rate (%)"},
    )
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig2.update_layout(
        coloraxis_showscale=False,
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Row 2: Quality trend over time 
st.subheader(" Quality Score Trend")

trend_dataset = st.selectbox(
    "Select dataset for trend",
    options=selected if selected else all_datasets,
    index=0,
)

trend_days = st.slider("Days to show", min_value=7, max_value=30, value=14)

trend_df = quality_trend(trend_dataset, trend_days)

if len(trend_df) > 0:
    fig3 = px.line(
        trend_df,
        x="date",
        y="score",
        markers=True,
        labels={"date": "Date", "score": "Quality Score"},
        color_discrete_sequence=["#2E86AB"],
    )
    fig3.add_hline(
        y=95, line_dash="dash", line_color="green",
        annotation_text="Clean target (~95)"
    )
    fig3.add_hline(
        y=70, line_dash="dash", line_color="orange",
        annotation_text="Mixed target (~70)"
    )
    fig3.add_hline(
        y=40, line_dash="dash", line_color="red",
        annotation_text="Messy target (~40)"
    )
    fig3.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_range=[0, 105],
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# Row 3: Monthly trend + Worst datasets 
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Monthly Quality Trends")

    monthly_filtered = monthly_df[monthly_df["dataset"].isin(selected)]

    fig4 = px.line(
        monthly_filtered,
        x="month",
        y="score",
        color="dataset",
        markers=True,
        labels={"month": "Month", "score": "Score", "dataset": "Dataset"},
    )
    fig4.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_range=[0, 105],
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig4, use_container_width=True)

with col_b:
    st.subheader(" Datasets Needing Attention")

    worst = worst_datasets(3)
    worst_filtered = worst[worst["dataset"].isin(selected)]

    if len(worst_filtered) == 0:
        st.success("All selected datasets are in good shape!")
    else:
        for _, row in worst_filtered.iterrows():
            score = row["score"]
            color = "🔴" if score < 50 else "🟡"
            st.metric(
                label=f"{color} {row['dataset']}",
                value=f"{score}/100",
                delta=f"{int(row['failed_rows'])} failed rows",
                delta_color="inverse",
            )

st.divider()

# Row 4: Full dataset comparison table 
st.subheader(" Dataset Comparison Table")

display_df = filtered_summary.copy()
display_df["pass_rate"] = display_df.apply(
    lambda r: f"{r['score']}%", axis=1
)
display_df["status"] = display_df["score"].apply(
    lambda s: " Good" if s >= 90 else "Fair" if s >= 60 else "Poor"
)

st.dataframe(
    display_df[["dataset", "total_rows", "passed_rows",
                "failed_rows", "score", "status"]],
    use_container_width=True,
    hide_index=True,
)