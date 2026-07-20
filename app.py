import streamlit as st
import pandas as pd
import psycopg2
import os
import json

def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

st.subheader("📈 AI Agent History & Evolution Over Time")
st.markdown("Tracking automated code architect reviews, pipeline changes, and compiled analytics workbooks across commits.")

try:
    conn = get_db_connection()
    query = """
        SELECT id, observation, created_at 
        FROM agent_memory 
        ORDER BY created_at DESC 
        LIMIT 50
    """
    df_mem = pd.read_sql(query, conn)
    conn.close()
    
    if not df_mem.empty:
        # Parse JSON observations stored in agent_memory
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
        
        # Filter controls
        event_types = df_history["Type"].unique().tolist()
        selected_type = st.selectbox("Filter by Report Type:", ["All"] + event_types)
        
        if selected_type != "All":
            df_history = df_history[df_history["Type"] == selected_type]
            
        # Display timeline table
        st.dataframe(
            df_history[["Time", "Type", "Title", "Summary"]],
            use_container_width=True,
            hide_index=True
        )
        
        # Timeline metrics chart
        st.markdown("### 📊 Activity Velocity")
        df_history['Date'] = pd.to_datetime(df_history['Time']).dt.date
        activity_counts = df_history.groupby('Date').size().reset_index(name='Reports Generated')
        st.bar_chart(activity_counts.set_index('Date'))

    else:
        st.info("No agent memory records found yet. Try making a git commit to trigger the post-commit reporting hook!")

except Exception as e:
    st.error(f"Could not load agent history from database: {e}")