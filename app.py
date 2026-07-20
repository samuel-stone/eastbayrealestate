import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="East Bay Real Estate Intelligence & Prospecting", layout="wide")

st.title("🏡 East Bay Real Estate Intelligence & Spatial Prospecting Dashboard")
st.markdown("Automated permit tracking, Haversine routing clusters, and local AI outreach strategies for Walnut Creek & Rossmoor.")

# Sidebar controls
st.sidebar.header("Navigation & Filters")
dataset_option = st.sidebar.selectbox(
    "Select Lead Dataset",
    ["scored_rossmoor_targets.csv", "moms_priority_local_leads.csv", "local_ai_analyzed_leads.csv"]
)

if os.path.exists(dataset_option):
    df = pd.read_csv(dataset_option)
else:
    df = pd.DataFrame({
        'address': ['1470 CREEKSIDE DR', '120 SUMMIT RD', '1948 3RD AVE'],
        'city': ['WALNUT CREEK', 'WALNUT CREEK', 'WALNUT CREEK'],
        'building_permit_count_24m': [10, 9, 9],
        'major_project_type': ['New Construction', 'Additions', 'Alterations'],
        'priority_score': [125, 115, 115]
    })

st.sidebar.info(f"Loaded {len(df)} properties from `{dataset_option}`.")

# Main KPI metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Prospect Targets", len(df))
if 'building_permit_count_24m' in df.columns:
    col2.metric("Average Permit Count", f"{df['building_permit_count_24m'].mean():.1f}")
if 'priority_score' in df.columns:
    col3.metric("Max Priority Score", f"{df['priority_score'].max():.0f}")

st.divider()

# Data Table view
st.subheader("📋 Filtered Lead Records")
search_query = st.text_input("Search Address or Project Type:", "")
if search_query:
    filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
else:
    filtered_df = df

st.dataframe(filtered_df, use_container_width=True)

# Visualizations
st.divider()
st.subheader("📊 Permit Momentum & Distribution")
if 'building_permit_count_24m' in df.columns:
    fig = px.histogram(df, x='building_permit_count_24m', nbins=10, title="Distribution of 24-Month Permits",
                       labels={'building_permit_count_24m': 'Permit Count'}, color_discrete_sequence=['#2b5c8f'])
    st.plotly_chart(fig, use_container_width=True)

# Local AI Trigger
st.divider()
st.subheader("🤖 Local AI Strategy Engine (Ollama / Llama 3)")
st.markdown("Run free local inference on your machine using Ollama in lieu of external API limits.")
if st.button("Run Local AI Analysis"):
    with st.spinner("Running local Llama inference..."):
        os.system("python3 local_ai_agent.py")
    st.success("Local AI analysis complete! Switch dataset selector to 'local_ai_analyzed_leads.csv' to review insights.")
