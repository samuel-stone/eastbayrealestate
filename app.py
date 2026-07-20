import streamlit as st
import pandas as pd
import os
import plotly.express as px
from code_architect import generate_proposals

st.set_page_config(page_title="East Bay Real Estate Intelligence & Prospecting", layout="wide")

st.title("🏡 East Bay Real Estate Intelligence & Spatial Prospecting Dashboard")
st.markdown("Automated permit tracking, Haversine routing clusters, and hybrid AI system architecture.")

# Sidebar navigation
st.sidebar.header("Navigation & Filters")
app_mode = st.sidebar.radio("Select View", ["Prospecting Pipeline", "🧠 AI Code Base Architect & Feature Proposals"])

if app_mode == "Prospecting Pipeline":
    dataset_option = st.sidebar.selectbox(
        "Select Lead Dataset",
        ["hybrid_ai_analyzed_leads.csv", "scored_rossmoor_targets.csv", "moms_priority_local_leads.csv", "local_ai_analyzed_leads.csv"]
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

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Prospect Targets", len(df))
    if 'building_permit_count_24m' in df.columns:
        col2.metric("Average Permit Count", f"{df['building_permit_count_24m'].mean():.1f}")
    if 'priority_score' in df.columns:
        col3.metric("Max Priority Score", f"{df['priority_score'].max():.0f}")

    st.divider()
    st.subheader("📋 Filtered Lead Records")
    search_query = st.text_input("Search Address or Project Type:", "")
    if search_query:
        filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)

    st.divider()
    st.subheader("📊 Permit Momentum & Distribution")
    if 'building_permit_count_24m' in df.columns:
        fig = px.histogram(df, x='building_permit_count_24m', nbins=10, title="Distribution of 24-Month Permits",
                           labels={'building_permit_count_24m': 'Permit Count'}, color_discrete_sequence=['#2b5c8f'])
        st.plotly_chart(fig, use_container_width=True)

elif app_mode == "🧠 AI Code Base Architect & Feature Proposals":
    st.subheader("🧠 Autonomous Codebase & Feature Expansion Architect")
    st.markdown("Analyze your repository structure using local Llama 3 or cloud Gemini escalation to generate architectural refactoring and feature roadmap proposals.")

    if st.button("Generate Codebase & Feature Proposals"):
        with st.spinner("Analyzing project files and consulting hybrid AI model..."):
            proposals, source = generate_proposals()
        st.success(f"Analysis generated successfully via {source}!")
        st.markdown(proposals)