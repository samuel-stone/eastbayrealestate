import os
import sys
import json
import subprocess
import hashlib
import urllib.request
import urllib.error

import pandas as pd
import streamlit as st
import plotly.express as px

# ---------------------------------------------------------
# Ensure project root is available for local architecture modules
# ---------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------
# Import local architecture agents & pooled core engine
# ---------------------------------------------------------
import code_architect
import analytics_architect
import business_proposal_architect
import avery_architect
import scraper_architect
import cma_architect
from core_engine import DatabasePool, fetch_dataframe

st.set_page_config(
    page_title="East Bay Real Estate & AI Architecture Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Design Improvements (Clean card layout, subtle shadows, modern palette)
# ---------------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
    div.stSelectbox > div[data-baseweb="select"] {
        border-radius: 6px;
    }
    .sidebar .sidebar-content {
        background-color: #f1f5f9;
    }
    .metric-card {
        background-color: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize centralized connection pool safely on startup
try:
    DatabasePool.initialize()
except Exception as e:
    st.error(f"Failed to initialize database connection pool: {e}")

st.title("🏡 East Bay Real Estate Autonomous Pipeline & AI Hub")
st.markdown("Live monitoring, municipal permit scraping, marketplace signal analysis, valuation CMAs, and real estate prospecting automation.")

# ---------------------------------------------------------
# Sidebar Navigation & Control Panel
# ---------------------------------------------------------
st.sidebar.header("System Control Panel")
model_choice = st.sidebar.text_input("Active Local LLM", value=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"))

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Navigation Hub")

nav_category = st.sidebar.radio(
    "Select Workspace",
    [
        "Agent History & Timeline",
        "Permits & Leads",
        "Motivated Sellers",
        "Spatial Velocity Map",
        "Live Scraper & Queue Monitor",
        "Autonomous Agent Health",
        "ROI & Direct Mail Estimator",
        "CMA Explorer",
        "SQL Console",
        "Codebase Architect",
        "Analytics Workstation",
        "AI Proposals",
        "Business Proposals",
        "Direct Mail & Labels"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Local AI & Model Status")
if st.sidebar.button("Test & Start Local Model"):
    with st.spinner("Pinging local Ollama engine & API daemon..."):
        service_active = False
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    service_active = True
        except Exception:
            pass
        
        if not service_active:
            try:
                res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    service_active = True
            except Exception:
                pass
                
        if service_active:
            st.sidebar.success(f"Ollama Engine is Active & Ready!\nTarget Model: {model_choice}")
        else:
            st.sidebar.error("Ollama service unreachable. Please ensure the Ollama app or daemon is running locally.")

# ---------------------------------------------------------
# NAVIGATION VIEWS
# ---------------------------------------------------------

if nav_category == "Agent History & Timeline":
    st.subheader("🤖 Agent History & Evolution Over Time")
    st.markdown("Tracking automated architecture reviews, scraper executions, pipeline changes, and compiled analytics workbooks across commits.")
    
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
                    obs = row['observation']
                    if isinstance(obs, str):
                        obs = json.loads(obs)
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
            event_types = ["All"] + df_history["Type"].unique().tolist()
            selected_type = st.selectbox("Filter by Report Type:", event_types)
            
            if selected_type != "All":
                df_history = df_history[df_history["Type"] == selected_type]
                
            st.dataframe(df_history[["Time", "Type", "Title", "Summary"]], use_container_width=True, hide_index=True)
            
            st.markdown("### 📊 Activity Velocity")
            df_history['Date'] = pd.to_datetime(df_history['Time']).dt.date
            activity_counts = df_history.groupby('Date').size().reset_index(name='Reports Generated')
            st.bar_chart(activity_counts.set_index('Date'))
        else:
            st.info("No agent memory records found yet. Run a scraper job or git commit to trigger activity logging!")
            
    except Exception as e:
        st.error(f"Could not load agent history from database: {e}")

elif nav_category == "Permits & Leads":
    st.subheader("📋 Active Prospect Leads & Permit Velocity")
    
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
                df_leads.head(15), x='address', y='permits_24m',
                title='Top 15 Properties by 24-Month Permit Velocity', color='permits_24m'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead data currently available in the database.")
    except Exception as e:
        st.error(f"Error loading leads data: {e}")

elif nav_category == "Motivated Sellers":
    st.subheader("🔥 Motivated Seller Intelligence Hub")
    st.markdown("Ranked leads based on marketplace signals: Price drops, high Days on Market (DOM), and deal fall-throughs.")
    
    try:
        with DatabasePool.get_connection() as conn:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor_check:
                cursor_check.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'marketplace_signals'
                    );
                """)
                res = cursor_check.fetchone()
                has_signals = res['exists'] if isinstance(res, dict) else res[0]
            
            if has_signals:
                query = """
                    SELECT l.address, l.city,
                           COALESCE(m.days_on_market, 0) as dom,
                           COALESCE(m.current_price, 0) as price,
                           COALESCE(m.price_drop_count, 0) as price_drops,
                           COALESCE(m.seller_motivation_score, 0) as motivation_score,
                           COALESCE(m.listing_status, 'Active') as status,
                           COALESCE(m.deal_fell_through, false) as deal_fell_through,
                           COALESCE(m.is_fixer_or_tlc, false) as is_fixer_or_tlc
                    FROM leads l
                    JOIN marketplace_signals m ON l.id = m.lead_id
                    ORDER BY motivation_score DESC, price_drops DESC
                    LIMIT 100
                """
            else:
                query = """
                    SELECT address, city, 
                           COALESCE(dom, 30) as dom,
                           COALESCE(price, 1000000) as price,
                           COALESCE(price_drops, 0) as price_drops,
                           (COALESCE(price_drops, 0) * 20 + 50) as motivation_score,
                           'Active' as status,
                           false as deal_fell_through,
                           COALESCE(is_fixer, false) as is_fixer_or_tlc
                    FROM properties
                    ORDER BY price DESC
                    LIMIT 100
                """
            df_motivated = pd.read_sql(query, conn)
            
        if not df_motivated.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Tracked Motivated Leads", len(df_motivated))
            col2.metric("Avg Days on Market", f"{int(df_motivated['dom'].mean())} days")
            col3.metric("Deals Fell Through", int(df_motivated['deal_fell_through'].sum()) if 'deal_fell_through' in df_motivated.columns else 0)
            
            st.dataframe(df_motivated, use_container_width=True, hide_index=True)
            
            fig_motivation = px.scatter(
                df_motivated, x="dom", y="price_drops", size="motivation_score", color="city",
                hover_name="address", title="Seller Motivation Matrix: Days on Market vs. Price Reductions"
            )
            st.plotly_chart(fig_motivation, use_container_width=True)
        else:
            st.warning("No marketplace signals recorded yet. Run your pipeline or migrations to populate motivation metrics!")
            
    except Exception as e:
        st.error(f"Marketplace signals module error: {e}")

elif nav_category == "Spatial Velocity Map":
    st.subheader("🗺️ Interactive Spatial Velocity Map")
    st.markdown("Visualizing high-velocity permit clusters and property coordinates across East Bay municipalities.")
    
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
            
            st.map(df_map, latitude="lat", longitude="lon", size="permits_24m", zoom=12)
            st.success(f"Successfully mapped {len(df_map)} individual property addresses across East Bay municipalities.")
        else:
            st.warning("No permit lead records found.")
    except Exception as e:
        st.error(f"Error loading interactive map: {e}")

elif nav_category == "Live Scraper & Queue Monitor":
    st.subheader("⚡ Live Municipal Permit & Redfin Pipeline Engine")
    st.markdown("Trigger modular Redfin extraction or municipal loaders, and monitor background worker queues in real-time.")
    
    scraper_jobs = {
        "Redfin Full Pipeline (Scrape -> Parse -> Enrich)": "scrape_redfin",
        "Redfin Scrape Only (scrape_redfin.py)": "redfin_scrape",
        "Redfin Enrich Only (enrich_redfin.py)": "redfin_enrich",
        "Walnut Creek Permits": "load_walnut_creek_permits",
        "Lafayette Permits": "load_lafayette_permits",
        "Rossmoor Permits": "load_rossmoor_permits",
        "Orinda Permits": "load_orinda_permits",
        "Zillow East Bay Comps": "load_zillow_comps",
    }
    
    selected_scraper_name = st.selectbox("Select Extraction / Pipeline Job", list(scraper_jobs.keys()))
    task_name = scraper_jobs[selected_scraper_name]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        trigger_btn = st.button("Queue Pipeline Job", type="primary")
        if trigger_btn:
            try:
                DatabasePool.initialize()
                with DatabasePool.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO jobs (name, status, created_at, attempts)
                            VALUES (%s, 'queued', NOW(), 0)
                        """, (task_name,))
                    conn.commit()
                st.success(f"Successfully queued {task_name}! Your background worker will pick it up shortly.")
            except Exception as e:
                st.error(f"❌ Failed to queue job: {e}")
                
    st.markdown("---")
    st.markdown("### 📊 Recent Worker Queue Status & Live Telemetry")
    
    try:
        DatabasePool.initialize()
        with DatabasePool.get_connection() as conn:
            df_jobs = pd.read_sql("""
                SELECT id, name, status, attempts, last_error, created_at, completed_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT 15
            """, conn)
            
            df_events = pd.read_sql("""
                SELECT id, job_id, event_type, message, created_at
                FROM execution_events
                ORDER BY created_at DESC
                LIMIT 15
            """, conn)
            
        if not df_jobs.empty:
            st.markdown("#### Job Queue")
            st.dataframe(df_jobs, use_container_width=True, hide_index=True)
        else:
            st.info("No background jobs found in queue.")
            
        if not df_events.empty:
            st.markdown("#### Worker Execution Events & Telemetry")
            st.dataframe(df_events, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.info(f"Could not load job queue telemetry: {e}")

elif nav_category == "Autonomous Agent Health":
    st.subheader("🩺 Autonomous Agent Health & Operations Console")
    st.markdown("System diagnostics, worker daemon heartbeat status, and task failure/success metrics.")
    
    try:
        DatabasePool.initialize()
        with DatabasePool.get_connection() as conn:
            df_job_stats = pd.read_sql("""
                SELECT status, COUNT(*) as count 
                FROM jobs 
                GROUP BY status
            """, conn)
            
            df_recent_fails = pd.read_sql("""
                SELECT id, name, last_error, created_at 
                FROM jobs 
                WHERE status = 'failed' 
                ORDER BY created_at DESC 
                LIMIT 10
            """, conn)
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Job Status Breakdown")
            if not df_job_stats.empty:
                st.dataframe(df_job_stats, use_container_width=True, hide_index=True)
                fig_stat = px.pie(df_job_stats, names='status', values='count', title="Worker Job Distribution by Status")
                st.plotly_chart(fig_stat, use_container_width=True)
            else:
                st.info("No job telemetry statistics available.")
                
        with col2:
            st.markdown("### Recent Job Failures & Errors")
            if not df_recent_fails.empty:
                st.dataframe(df_recent_fails, use_container_width=True, hide_index=True)
            else:
                st.success("🎉 No recent job failures recorded! All worker pipelines running clean.")
    except Exception as e:
        st.error(f"Error loading health metrics: {e}")

elif nav_category == "ROI & Direct Mail Estimator":
    st.subheader("💰 ROI & Direct Mail Campaign Estimator")
    st.markdown("Forecast direct mail marketing campaign economics, response rates, and expected gross acquisition profit.")
    
    col1, col2 = st.columns(2)
    with col1:
        mail_pieces = st.number_input("Number of Mailers / Postcards Sent", min_value=100, max_value=10000, value=1000, step=100)
        cost_per_mailer = st.number_input("Cost per Mailer ($)", min_value=0.50, max_value=5.00, value=1.20, step=0.10)
        expected_response_rate = st.slider("Expected Response Rate (%)", min_value=0.1, max_value=5.0, value=1.2, step=0.1)
    with col2:
        conversion_rate = st.slider("Lead Conversion Rate (%)", min_value=1.0, max_value=25.0, value=10.0, step=1.0)
        avg_deal_profit = st.number_input("Estimated Net Profit per Deal ($)", min_value=10000, max_value=150000, value=35000, step=5000)
        
    if st.button("Calculate Campaign Projections"):
        total_cost = mail_pieces * cost_per_mailer
        expected_responses = int(mail_pieces * (expected_response_rate / 100.0))
        expected_deals = max(1, int(expected_responses * (conversion_rate / 100.0)))
        total_gross_profit = expected_deals * avg_deal_profit
        net_roi_profit = total_gross_profit - total_cost
        roi_percentage = (net_roi_profit / total_cost) * 100 if total_cost > 0 else 0
        
        st.markdown("---")
        st.markdown("### 📊 Campaign Financial Forecast")
        rcol1, rcol2, rcol3, rcol4 = st.columns(4)
        rcol1.metric("Total Campaign Budget", f"${total_cost:,.2f}")
        rcol2.metric("Expected Responses", f"{expected_responses} leads")
        rcol3.metric("Projected Closed Deals", f"{expected_deals} deals")
        rcol4.metric("Net Campaign ROI", f"{roi_percentage:,.1f}%", f"${net_roi_profit:,.2f}")
        
        st.success(f"Based on your inputs, sending {mail_pieces} mailers is projected to generate ~{expected_responses} inbound responses and approximately {expected_deals} closed transaction(s), yielding an estimated net return of **${net_roi_profit:,.2f}**.")

elif nav_category == "CMA Explorer":
    st.subheader("📈 Comparable Market Analysis (CMA) Pricing Explorer")
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

elif nav_category == "SQL Console":
    st.subheader("💻 Database SQL Console")
    query_options = {
        "Custom Query...": "",
        "Count Leads by City": "SELECT city, COUNT(*) FROM leads GROUP BY city ORDER BY count DESC;",
        "Recent Marketplace Signals": "SELECT * FROM marketplace_signals ORDER BY updated_at DESC LIMIT 10;",
        "Check Agent Memory Entries": "SELECT id, source_agent, created_at FROM agent_memory ORDER BY created_at DESC LIMIT 10;",
    }
    selected_shortcut = st.selectbox("Quick Query Presets", list(query_options.keys()))
    default_query = query_options[selected_shortcut]
    
    query = st.text_area("SQL Query", value=default_query, height=120)
    if st.button("▶ Run Query", type="primary"):
        if query.strip():
            try:
                DatabasePool.initialize()
                with DatabasePool.get_connection() as conn:
                    df = pd.read_sql(query, conn)
                st.success(f"Query executed successfully! Returned {len(df)} rows.")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Query Error: {e}")

elif nav_category == "Codebase Architect":
    st.subheader("🛠️ Local AI Codebase Architect")
    st.markdown("Run a live architectural inspection of your repository code using your local Ollama instance.")
    
    if st.button("Run Codebase Review & Proposals"):
        with st.spinner("AI Architect is analyzing repository files..."):
            try:
                result, source = code_architect.generate_proposals()
                st.success(f"Analysis generated successfully via {source}!")
                st.markdown(result)
            except Exception as e:
                st.error(f"Code Architect failed: {e}")

elif nav_category == "Analytics Workstation":
    st.subheader("🔬 Advanced Analytics Workstation & Model Studio")
    analysis_mode = st.selectbox("Select Analytics Engine", [
        "Descriptive Lead Statistics",
        "Permit Concentration Heatmap Data",
        "Custom Pandas Query Runner"
    ])
    
    try:
        DatabasePool.initialize()
        with DatabasePool.get_connection() as conn:
            df_full = pd.read_sql("""
                SELECT l.id, l.address, l.city, l.status,
                       COALESCE(f.building_permit_count_24m, 0) as permits_24m,
                       COALESCE(f.project_count, 0) as projects
                FROM leads l
                LEFT JOIN prospect_features f ON l.id = f.lead_id
            """, conn)
            
        if analysis_mode == "Descriptive Lead Statistics":
            st.markdown("### Statistical Breakdown of Active Leads")
            if not df_full.empty:
                st.dataframe(df_full.describe(), use_container_width=True)
                city_breakdown = df_full.groupby('city').agg(
                    Total_Leads=('id', 'count'),
                    Avg_Permits=('permits_24m', 'mean'),
                    Total_Permits=('permits_24m', 'sum')
                ).reset_index()
                st.markdown("### Municipal Summary Table")
                st.dataframe(city_breakdown, use_container_width=True, hide_index=True)
            else:
                st.warning("No lead records available.")
                
        elif analysis_mode == "Permit Concentration Heatmap Data":
            st.markdown("### Permit Distribution Analysis")
            if not df_full.empty:
                fig_hist = px.histogram(df_full, x="permits_24m", color="city", barmode="group", title="Permit Count Distribution by Municipality")
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.warning("No lead records available.")
                
        elif analysis_mode == "Custom Pandas Query Runner":
            st.markdown("### 🐍 Interactive Pandas DataFrame Operations")
            user_code = st.text_area("Enter Pandas Filtering Expression", value="df_full.sort_values(by='permits_24m', ascending=False).head(20)")
            if st.button("Execute Pandas Expression"):
                try:
                    result_df = eval(user_code)
                    st.success("Executed successfully!")
                    st.dataframe(result_df, use_container_width=True)
                except Exception as eval_err:
                    st.error(f"Evaluation Error: {eval_err}")
    except Exception as e:
        st.error(f"Analytics Workstation error connecting to database: {e}")

elif nav_category == "AI Proposals":
    st.subheader("💡 AI-Generated Refactoring & Architecture Proposals")
    st.markdown("Review architectural recommendations logged by your automated post-commit agent memory.")
    
    try:
        with DatabasePool.get_connection() as conn:
            df_props = pd.read_sql("""
                SELECT id,
                       observation,
                       created_at,
                       COALESCE(status, 'pending') as status,
                       COALESCE(execution_output, '') as execution_output
                FROM agent_memory
                WHERE (observation::jsonb)->>'type' = 'proposal'
                   OR (observation::jsonb)->>'title' IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 10
            """, conn)
            
        if not df_props.empty:
            for _, row in df_props.iterrows():
                try:
                    obs = row['observation']
                    if isinstance(obs, str):
                        obs = json.loads(obs)
                    status = row['status']
                    title = obs.get('title', 'AI Proposal')
                    expander_label = f"📌 {title} ({row['created_at']})"
                    if status == 'executed':
                        expander_label += " ✔ [SANDBOX TESTED]"
                        
                    with st.expander(expander_label):
                        st.markdown(f"**Proposal Summary:** {obs.get('summary', 'No summary available.')}")
                        diff_text = obs.get("full_proposal") or obs.get("diff")
                        if diff_text:
                            st.markdown("**Proposed Details / Code Review:**")
                            st.code(diff_text, language="markdown")
                            
                        if status == 'executed':
                            st.success("Sandbox check ran for this proposal.")
                            if row['execution_output']:
                                st.markdown("**Audit Log:**")
                                st.code(row['execution_output'], language=None)
                except Exception as parse_err:
                    st.error(f"Error rendering proposal item: {parse_err}")
        else:
            st.info("No proposals generated yet. Run Codebase Review in the Architect tab to populate this list!")
    except Exception as e:
        st.error(f"Error loading proposals: {e}")

elif nav_category == "Business Proposals":
    st.subheader("📑 Client Prospecting & Property Valuation Architect")
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
            st.success("Proposal successfully drafted!")
            st.markdown(proposal_text)
            st.download_button(
                label="📥 Download Client Proposal (.md)",
                data=proposal_text,
                file_name=f"property_proposal_{target_city_input.lower().replace(' ', '_')}.md",
                mime="text/markdown"
            )

elif nav_category == "Direct Mail & Labels":
    st.subheader("🏷️ Avery Mailing Labels & Direct Mail Export")
    st.markdown("Export formatted property address CSV sheets tailored for Avery standard mailing labels (e.g. Avery 5160).")
    
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