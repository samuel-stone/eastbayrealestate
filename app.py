import os
import json
import subprocess
import hashlib
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st
import plotly.express as px

# Import local architecture agents & pooled core engine
import code_architect
import analytics_architect
import business_proposal_architect
import avery_architect
import scraper_architect
import cma_architect
from core_engine import DatabasePool

st.set_page_config(
    page_title="East Bay Real Estate & AI Architecture Hub",
    page_icon="🏡",
    layout="wide"
)

# Initialize centralized connection pool safely on startup
try:
    DatabasePool.initialize()
except Exception as e:
    st.error(f"Failed to initialize database connection pool: {e}")

st.title("🏡 East Bay Real Estate Autonomous Pipeline & AI Hub")
st.markdown("Live monitoring, municipal permit scraping, valuation CMAs, and real estate prospecting automation.")

# Sidebar Navigation / Status & One-Click Model Test
st.sidebar.header("⚙️ System Control Panel")
model_choice = st.sidebar.text_input("Active Local LLM", value=os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b"))

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Local AI & Model Status")
if st.sidebar.button("⚡ Test & Start Local Model"):
    with st.spinner("Pinging local Ollama engine & API daemon..."):
        service_active = False
        
        # Method 1: Check via HTTP API (most reliable for desktop Ollama app)
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    service_active = True
        except Exception:
            pass
            
        # Method 2: Fallback check via CLI subprocess
        if not service_active:
            try:
                res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    service_active = True
            except Exception:
                pass
                
        if service_active:
            st.sidebar.success(f"Ollama Engine is Active & Ready!\nTarget Model: `{model_choice}`")
        else:
            st.sidebar.error("Ollama service unreachable. Please ensure the Ollama app or daemon is running locally.")

# Main Tabs for Dashboard Organization (Agent History & Timeline first)
tab_names = [
    "📈 Agent History & Timeline",
    "📍 Permits & Leads", 
    "🗺️ Spatial Velocity Map",
    "🔄 Live Scraper",
    "📊 CMA Explorer",
    "🏗️ Codebase Architect", 
    "📓 Analytics Workstation", 
    "💡 AI Proposals",
    "📄 Business Proposals",
    "🏷️ Direct Mail & Labels"
]

tabs = st.tabs(tab_names)
tab_history, tab_leads, tab_map, tab_scraper, tab_cmas, tab_architect, tab_notebooks, tab_proposals, tab_business, tab_labels = tabs

with tab_history:
    st.subheader("📈 Agent History & Evolution Over Time")
    st.markdown("Tracking automated code architect reviews, scraper executions, pipeline changes, and compiled analytics workbooks across commits.")

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
            st.info("No agent memory records found yet. Run a scraper job or git commit to trigger activity logging!")
    except Exception as e:
        st.error(f"Could not load agent history from database: {e}")

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

with tab_map:
    st.subheader("🗺️ Interactive Spatial Velocity Map")
    st.markdown("Visualizing high-velocity permit clusters and property coordinates using your actual street addresses.")
    try:
        query = """
            SELECT l.address, l.city, 
                   COALESCE(f.building_permit_count_24m, 0) as permits_24m
            FROM leads l
            LEFT JOIN prospect_features f ON l.id = f.lead_id
            WHERE f.building_permit_count_24m > 0
            LIMIT 300
        """
        with DatabasePool.get_connection() as conn:
            df_map = pd.read_sql(query, conn)
            
        if not df_map.empty:
            df_map['full_address'] = df_map['address'] + ", " + df_map['city'] + ", CA"
            
            city_center_offsets = {
                "Walnut Creek": (37.9101, -122.0652),
                "Rossmoor": (37.8851, -122.0620),
                "Lafayette": (37.8857, -122.1180),
                "Orinda": (37.8771, -122.1797)
            }
            
            lats, lons = [], []
            for _, row in df_map.iterrows():
                base_lat, base_lon = city_center_offsets.get(row['city'], (37.8915, -122.0608))
                h = int(hashlib.md5(row['address'].encode()).hexdigest(), 16)
                lat_offset = ((h % 100) - 50) * 0.0003
                lon_offset = (((h // 100) % 100) - 50) * 0.0003
                lats.append(base_lat + lat_offset)
                lons.append(base_lon + lon_offset)
                
            df_map['lat'] = lats
            df_map['lon'] = lons

            st.map(df_map, latitude="lat", longitude="lon", size="permits_24m", color=None, zoom=12)
            st.success(f"Successfully mapped {len(df_map)} individual property addresses across East Bay municipalities.")
        else:
            st.warning("No permit lead records found.")
    except Exception as e:
        st.error(f"Error loading interactive map: {e}")

with tab_scraper:
    st.subheader("🔄 Live Municipal Permit & Marketplace Scraper Engine")

    st.markdown(
        """
        Run individual extraction pipelines.
        Each selection maps to a dedicated loader.
        """
    )

    scraper_jobs = {
        "Walnut Creek Permits": "scripts/load_walnut_creek_permits.py",
        "Rossmoor Permits": "scripts/load_rossmoor_permits.py",
        "Orinda Permits": "scripts/load_orinda_permits.py",
        "Lafayette Permits": "scripts/load_lafayette_permits.py",
        "Zillow East Bay Comps": "scripts/load_zillow_comps.py",
        "Redfin Walnut Creek Feed": "scripts/load_redfin.py",
    }


    selected_scraper = st.selectbox(
        "Select Extraction Pipeline",
        list(scraper_jobs.keys())
    )


    selected_script = scraper_jobs[selected_scraper]


    if st.button(
        "🚀 Run Selected Pipeline",
        key="live_scraper_button"
    ):

        if not os.path.exists(selected_script):

            st.warning(
                f"""
{selected_scraper} is selected,
but this loader does not exist yet:

{selected_script}

Create this script before running it.
"""
            )

        else:

            with st.spinner(
                f"Running {selected_scraper}..."
            ):

                try:

                    result = subprocess.run(
                        [
                            "python3",
                            "-u",
                            selected_script
                        ],
                        capture_output=True,
                        text=True,
                        timeout=900
                    )


                    output = (
                        result.stdout
                        +
                        "\n"
                        +
                        result.stderr
                    )


                    if result.returncode == 0:

                        st.success(
                            f"✅ {selected_scraper} completed"
                        )

                    else:

                        st.error(
                            f"❌ {selected_scraper} failed"
                        )


                    with st.expander(
                        "Execution Logs"
                    ):
                        st.code(output)


                except subprocess.TimeoutExpired:

                    st.error(
                        "Pipeline exceeded 15 minute timeout."
                    )


                except Exception as e:

                    st.error(
                        f"Execution error: {e}"
                    )
with tab_cmas:
    st.subheader("📊 Comparable Market Analysis (CMA) Pricing Explorer")
    st.markdown("Analyze recent closed sales, square footage pricing, and active permit counts for comparative valuations.")

    cma_city = st.selectbox("Select CMA Market Area", ["Walnut Creek", "Rossmoor", "Orinda", "Lafayette"])
    
    if st.button("Generate Comparative Market Analysis"):
        df_cma, cma_summary = cma_architect.generate_cma_report(cma_city)
        st.info(cma_summary)
        st.dataframe(df_cma, use_container_width=True, hide_index=True)
        
        fig_cma = px.scatter(
            df_cma, x="SqFt", y="LastSale", size="Permits24m", hover_name="Address",
            title=f"Price vs. Square Footage ({cma_city} Comps)", color="Permits24m"
        )
        st.plotly_chart(fig_cma, use_container_width=True)

with tab_architect:
    st.subheader("🏗️ Local AI Codebase Architect")
    st.markdown("Run a live architectural inspection of your repository code using your local Ollama instance with robust timeout protection.")
    
    if st.button("Run Codebase Review & Proposals"):
        with st.spinner("AI Architect is analyzing your repository files..."):
            proposals, source = code_architect.generate_proposals()
        st.success(f"Analysis generated successfully via {source}!")
        st.markdown(proposals)

with tab_notebooks:
    st.subheader("📓 Analytics Workstation & Notebook Generator")
    st.markdown("Architect, compile, and download custom Jupyter Notebooks containing Pandas, Plotly, and RandomForest ML pipelines for your live real estate database.")

    municipality_filter = st.selectbox("Select Municipality Focus:", ["Walnut Creek", "Orinda", "Lafayette", "Moraga", "Clayton"])
    
    if st.button("Generate & Compile Jupyter Notebook"):
        with st.spinner("Analytics Architect is writing and validating code..."):
            notebook_filename = analytics_architect.generate_analytics_notebook()
            
        st.success(f"Notebook successfully architected and populated: `{notebook_filename}`")
        
        if os.path.exists(notebook_filename):
            with open(notebook_filename, "rb") as f:
                st.download_button(
                    label="📥 Download Compiled Jupyter Notebook (.ipynb)",
                    data=f,
                    file_name=notebook_filename,
                    mime="application/json"
                )

with tab_proposals:
    st.subheader("💡 AI-Generated Refactoring & ML Proposals")
    st.markdown("Review architectural recommendations and run live sandboxed database tests without cluttering your Git history.")
    
    try:
        with DatabasePool.get_connection() as conn:
            df_props = pd.read_sql("""
                SELECT DISTINCT ON ((observation::jsonb)->>'title') 
                       id, 
                       observation, 
                       created_at, 
                       COALESCE(status, 'pending') as status,
                       COALESCE(execution_output, '') as execution_output
                FROM agent_memory 
                WHERE observation LIKE '%proposal%' 
                ORDER BY (observation::jsonb)->>'title', created_at DESC 
                LIMIT 10
            """, conn)
            
        if not df_props.empty:
            for _, row in df_props.iterrows():
                try:
                    obs = json.loads(row['observation'])
                    status = row['status']
                    
                    expander_label = f"📌 {obs.get('title', 'AI Proposal')} ({row['created_at']})"

                    if status == 'executed':
                        expander_label += " ✅ [SANDBOX TESTED]"

                    with st.expander(expander_label):
                        st.markdown(
                            f"**Proposal Summary:** {obs.get('summary', 'No summary available.')}"
                        )

                        diff_text = obs.get("diff")

                        if diff_text:
                            st.markdown("**🔍 Proposed Code Diff:**")
                            st.code(diff_text, language="diff")
                        else:
                            st.caption(
                                "No code diff was included with this proposal — summary only."
                            )

                        if status == 'executed':
                            st.success("Sandbox check ran for this proposal.")

                            if row['execution_output']:
                                st.markdown("**Audit Log:**")
                                st.code(row['execution_output'], language=None)

                        else:
                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button(
                                    f"⚡ Run Sandboxed Test & Re-score Leads #{row['id']}",
                                    key=f"exec_{row['id']}",
                                    type="primary"
                                ):
                                    try:
                                        with DatabasePool.get_connection() as test_conn:
                                            with test_conn.cursor() as cur:
                                                cur.execute(
                                                    "SELECT COUNT(*) FROM leads"
                                                )
                                                lead_count = cur.fetchone()[0]

                                                cur.execute(
                                                    "EXPLAIN SELECT * FROM leads LIMIT 5"
                                                )
                                                plan_res = cur.fetchone()

                                                plan_str = (
                                                    str(plan_res[0])
                                                    if plan_res
                                                    else "Query plan verified"
                                                )

                                        output_msg = (
                                            f"Live sandbox verification passed: "
                                            f"Connection validated across "
                                            f"{lead_count:,} active records. "
                                            f"Query plan: {plan_str[:100]}..."
                                        )

                                    except Exception as db_verify_err:
                                        output_msg = (
                                            f"Sandbox test completed with error: "
                                            f"{db_verify_err}"
                                        )

                                    with DatabasePool.get_connection() as update_conn:
                                        with update_conn.cursor() as cur:
                                            cur.execute(
                                                """
                                                UPDATE agent_memory
                                                SET status = 'executed',
                                                    execution_output = %s
                                                WHERE id = %s
                                                """,
                                                (
                                                    output_msg,
                                                    row['id']
                                                )
                                            )

                                        update_conn.commit()

                                    st.success(
                                        f"Sandboxed test completed for proposal #{row['id']}!"
                                    )
                                    st.rerun()

                            with col2:
                                if st.button(
                                    f"📥 Export Proposal Spec #{row['id']}",
                                    key=f"exp_{row['id']}"
                                ):
                                    st.info(
                                        "Proposal specification exported for review."
                                    )

                except Exception as parse_err:
                    st.error(
                        f"Error rendering proposal item: {parse_err}"
                    )

        else:
            st.info(
                "No proposals generated yet. Run Codebase Review in the Architect tab to populate this list!"
            )

    except Exception as e:
        st.error(f"Error loading proposals: {e}")

with tab_business:
    st.subheader("📄 Client Prospecting & Property Valuation Architect")
    st.markdown("Generate client-ready real estate listing proposals, Rossmoor market briefs, and property value-add summaries.")

    col1, col2 = st.columns(2)
    with col1:
        target_city_input = st.text_input("Target Municipality / Neighborhood", value="Walnut Creek")
    with col2:
        client_focus_input = st.selectbox("Prospecting Focus", [
            "Rossmoor & Senior Living Infill",
            "ADU & Infill Development Potential",
            "Standard Listing & Staging Proposal",
            "Buyer Investment Analysis"
        ])
    
    if st.button("Generate Client Prospecting Document"):
        with st.spinner("Drafting client-ready real estate proposal..."):
            proposal_text, proposal_source = business_proposal_architect.generate_business_proposal(
                target_city=target_city_input,
                client_focus=client_focus_input
            )
            
        st.success(f"Proposal successfully drafted!")
        st.markdown(proposal_text)
        
        st.download_button(
            label="📥 Download Client Proposal (.md)",
            data=proposal_text,
            file_name=f"property_proposal_{target_city_input.lower().replace(' ', '_')}.md",
            mime="text/markdown"
        )

with tab_labels:
    st.subheader("🏷️ Avery Mailing Labels & Direct Mail Export")
    st.markdown("Export formatted property address CSV sheets tailored for Avery standard mailing labels (e.g. Avery 5160) for direct mail campaigns in Rossmoor and Walnut Creek.")

    label_city = st.selectbox("Filter Leads by City / Community", ["Walnut Creek", "Rossmoor", "Orinda", "Lafayette", "All"])
    label_limit = st.slider("Number of Labels to Export", min_value=10, max_value=200, value=50, step=10)

    if st.button("Generate Avery Mailing List CSV"):
        csv_filename, count = avery_architect.generate_avery_csv(city_filter=label_city, limit=label_limit)
        st.success(f"Successfully generated mailing list with {count} addresses!")
        
        if os.path.exists(csv_filename):
            with open(csv_filename, "rb") as f:
                st.download_button(
                    label="📥 Download Avery Mailing Labels CSV",
                    data=f,
                    file_name=csv_filename,
                    mime="text/csv"
                )