import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# Import local architecture agents & pooled core engine
import code_architect
import analytics_architect
from core_engine import DatabasePool, execute_query

st.set_page_config(
    page_title="East Bay Real Estate & AI Architecture Hub",
    page_icon="🏡",
    layout="wide"
)

# Initialize the centralized connection pool safely on startup
try:
    DatabasePool.initialize()
except Exception as e:
    st.error(f"Failed to initialize database connection pool: {e}")

st.title("🏡 East Bay Real Estate Autonomous Pipeline & AI Hub")
st.markdown("Live monitoring, local Llama 3.2 architectural oversight, and automated data science pipelines.")

# Sidebar Navigation / Status
st.sidebar.header("⚙️ System Control Panel")
model_choice = st.sidebar.text_input("Active Local LLM", value=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"))

# Main Tabs for Dashboard Organization
tab_leads, tab_architect, tab_notebooks, tab_history = st.tabs([
    "📍 Permits & Leads", 
    "🏗️ Codebase Architect", 
    "📓 Analytics Notebooks", 
    "📈 Agent History & Timeline"
])

with tab_leads:
    st.subheader("Active Prospect Leads & Permit Velocity")
    try:
        query = """
            SELECT l.id, l.address, l.city, l.status, 
                   COALESCE(f.building_permit_count_24m, 0) as permits_24m,
                   COALESCE(f.project_count, 0) as projects
            FROM leads l
            LEFT JOIN prospect_features f ON l.id = f.lead_id
            ORDER BY permits_24m DESC
            LIMIT 100
        """
        with DatabasePool.get_connection() as conn:
            df_leads = pd.read_sql(query, conn)
        
        if not df_leads.empty:
            st.dataframe(df_leads, use_container_width=True, hide_index=True)
            
            # Quick Visualization
            fig = px.bar(
                df_leads.head(15), 
                x='address', 
                y='permits_24m', 
                title='Top 15 Properties by 24-Month Permit Velocity',
                color='permits_24m'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead data currently available in the database.")
    except Exception as e:
        st.error(f"Error loading leads data: {e}")

with tab_architect:
    st.subheader("🏗️ Local AI Codebase Architect (Llama 3.2)")
    st.markdown("Run a live architectural inspection of your repository code using your local Ollama instance.")
    
    if st.button("Run Codebase Review & Proposals"):
        with st.spinner("Llama is analyzing your repository files..."):
            proposals, source = code_architect.generate_proposals()
        st.success(f"Analysis generated successfully via {source}!")
        st.markdown(proposals)

with tab_notebooks:
    st.subheader("📓 AI Analytics Architect & Notebook Generator")
    st.markdown("Have Llama architect and populate a custom Jupyter Notebook containing Pandas and Plotly pipelines for your live real estate database.")

    if st.button("Generate & Compile Jupyter Notebook"):
        with st.spinner("Analytics Architect is writing and validating code..."):
            notebook_filename = analytics_architect.generate_analytics_notebook()
            
        st.success(f"Notebook successfully architected and populated: `{notebook_filename}`")
        
        if os.path.exists(notebook_filename):
            with open(notebook_filename, "rb") as f:
                st.download_button(
                    label="📥 Download Generated Jupyter Notebook (.ipynb)",
                    data=f,
                    file_name=notebook_filename,
                    mime="application/json"
                )

with tab_history:
    st.subheader("📈 AI Agent History & Evolution Over Time")
    st.markdown("Tracking automated code architect reviews, pipeline changes, and compiled analytics workbooks across commits.")

    try:
        query = """
            SELECT id, observation, created_at 
            FROM agent_memory 
            ORDER BY created_at DESC 
            LIMIT 50
        """
        with DatabasePool.get_connection() as conn:
            df_mem = pd.read_sql(query, conn)
        
        if not df_mem.empty:
            parsed_records = []
            for _, row in df_mem.iterrows():
                try:
                    obs = json.loads(row['observation'])
                    parsed_records.append({
                        "ID": row['id'],
                        "Time": row['created_at'],
                        "Type": obs.get("type", "general"),
                        "Title": obs.get("title", "AI Observation"),
                        "Summary": obs.get("summary", str(obs))
                    })
                except Exception:
                    parsed_records.append({
                        "ID": row['id'],
                        "Time": row['created_at'],
                        "Type": "raw",
                        "Title": "System Event",
                        "Summary": str(row['observation'])
                    })
                    
            df_history = pd.DataFrame(parsed_records)
            
            event_types = df_history["Type"].unique().tolist()
            selected_type = st.selectbox("Filter by Report Type:", ["All"] + event_types)
            
            if selected_type != "All":
                df_history = df_history[df_history["Type"] == selected_type]
                
            st.dataframe(
                df_history[["Time", "Type", "Title", "Summary"]],
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("### 📊 Activity Velocity")
            df_history['Date'] = pd.to_datetime(df_history['Time']).dt.date
            activity_counts = df_history.groupby('Date').size().reset_index(name='Reports Generated')
            st.bar_chart(activity_counts.set_index('Date'))
        else:
            st.info("No agent memory records found yet. Make a git commit to trigger the post-commit reporting hook!")
    except Exception as e:
        st.error(f"Could not load agent history from database: {e}")