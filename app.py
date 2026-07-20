import streamlit as st
import pandas as pd
import os
import psycopg2
import plotly.express as px
import time

st.set_page_config(page_title="East Bay Real Estate Intelligence & Prospecting", layout="wide")

st.title("🏡 East Bay Real Estate Intelligence & Spatial Prospecting")
st.markdown("Automated permit tracking, routing clusters, and local AI outreach strategies for Walnut Creek & Rossmoor, prioritizing surprise mystery sets.")

# --- Database Connection & Caching ---
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

@st.cache_data(ttl=5) # Reduced cache time to 5 seconds to support live refreshing
def fetch_data(query):
    conn = get_db_connection()
    return pd.read_sql(query, conn)

def queue_ai_job():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO jobs (name, status, created_at, attempts) VALUES ('local_ai_analysis', 'queued', NOW(), 0)")
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# --- Data Fetching ---
try:
    df = fetch_data("""
        SELECT 
            l.address, l.city, l.status, 
            COALESCE(f.building_permit_count_24m, 0) as building_permit_count_24m,
            COALESCE(f.project_count, 0) as project_count
        FROM leads l
        LEFT JOIN prospect_features f ON l.id = f.lead_id
        ORDER BY building_permit_count_24m DESC
        LIMIT 500
    """)
    
    jobs_df = fetch_data("SELECT id, name, status, created_at, attempts, last_error FROM jobs ORDER BY created_at DESC LIMIT 10")
    status_df = fetch_data("SELECT name, status, COUNT(*) as total FROM jobs GROUP BY name, status ORDER BY name")
    
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")
    df = pd.DataFrame()
    jobs_df = pd.DataFrame()
    status_df = pd.DataFrame()

# --- Sidebar Controls ---
st.sidebar.header("Navigation & Filters")
st.sidebar.info(f"Currently tracking {len(df)} live properties from the database.")

st.sidebar.divider()
auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh (10s)", value=False, help="Automatically reload the dashboard every 10 seconds to watch the AI queue in real-time.")

# --- Main KPI Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Prospect Targets", len(df))
if not df.empty and 'building_permit_count_24m' in df.columns:
    col2.metric("Average Permit Count", f"{df['building_permit_count_24m'].mean():.1f}")
if not df.empty and 'project_count' in df.columns:
    col3.metric("Max Project Count", f"{df['project_count'].max():.0f}")

st.divider()

# --- Data Table View ---
st.subheader("📋 Filtered Lead Records")
search_query = st.text_input("Search Address or City:", "")
if search_query and not df.empty:
    filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
else:
    filtered_df = df

st.dataframe(filtered_df, use_container_width=True)

st.divider()

# --- Visualizations ---
st.subheader("📊 Permit Momentum & Distribution")
if not df.empty and 'building_permit_count_24m' in df.columns:
    fig = px.histogram(df, x='building_permit_count_24m', nbins=10, title="Distribution of 24-Month Permits",
                       labels={'building_permit_count_24m': 'Permit Count'}, color_discrete_sequence=['#2b5c8f'])
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- AI Task Memory & Queue Status ---
st.subheader("🧠 AI Agent Memory & Queue Status")
st.markdown("Live view of backend automation tasks and worker pipeline.")

col_a, col_b = st.columns([2, 1])
with col_a:
    st.write("**Recent Task Execution Memory**")
    st.dataframe(jobs_df, use_container_width=True)
with col_b:
    st.write("**Aggregate System Status**")
    st.dataframe(status_df, use_container_width=True)

st.divider()

# --- Local AI Trigger ---
st.subheader("🤖 Local AI Strategy Engine")
st.markdown("Queue local inference tasks to your backend worker.")
if st.button("Queue AI Analysis"):
    with st.spinner("Adding task to queue..."):
        success = queue_ai_job()
    if success:
        st.success("Task successfully queued! The backend agent will pick it up shortly.")

# --- Auto-Refresh Logic ---
if auto_refresh:
    time.sleep(10)
    st.rerun()