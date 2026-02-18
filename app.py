import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =============================
# ENVIRONMENT & CONFIG
# =============================
load_dotenv()

st.set_page_config(
    page_title="General Ledger Dashboard", 
    page_icon="💠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# CUSTOM CSS (PRODUCTION UI/UX)
# =============================
st.markdown("""
<style>
    /* Global Backgrounds & Typography */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Hero Banner for Logged Out State */
    .hero-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 5rem 3rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .hero-banner h1 { color: white; font-size: 3.5rem; font-weight: 800; line-height: 1.2; margin-bottom: 1rem; }
    .hero-banner p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 0; color: #E0F2FE;}
    
    /* Feature Cards */
    .feature-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        height: 100%;
    }
    .feature-icon { font-size: 2.5rem; margin-bottom: 1rem; }
    .feature-title { font-weight: 700; color: #1E293B; margin-bottom: 0.5rem; }
    .feature-text { color: #64748B; font-size: 0.95rem; }

    /* Main Dashboard Header */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
    }

    /* Custom Gradient KPI Cards */
    .kpi-container {
        display: flex;
        flex-direction: column;
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    .kpi-container:hover { transform: translateY(-5px); }
    .kpi-title { font-size: 1rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; }
    .kpi-value { font-size: 2rem; font-weight: 700; line-height: 1.1; margin-bottom: 0.5rem; }
    .kpi-sub { font-size: 0.85rem; font-weight: 500; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; display: inline-block; }
    
    .bg-revenue { background: linear-gradient(135deg, #10B981 0%, #059669 100%); }
    .bg-expense { background: linear-gradient(135deg, #F43F5E 0%, #E11D48 100%); }
    .bg-profit { background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); }
    .bg-margin { background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%); }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
    }
    
    /* Date Range Toggle */
    .date-range-toggle {
        background-color: #F1F5F9;
        padding: 0.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# AUTHENTICATION & API LOGIC
# =============================
@st.cache_resource
def get_credential():
    return ClientSecretCredential(
        tenant_id=os.getenv("FABRIC_TENANT_ID"),
        client_id=os.getenv("FABRIC_CLIENT_ID"),
        client_secret=os.getenv("FABRIC_CLIENT_SECRET")
    )

def get_access_token():
    credential = get_credential()
    token = credential.get_token("https://api.fabric.microsoft.com/.default")
    return token.token

def run_graphql(query, variables=None):
    endpoint = os.getenv("FABRIC_ENDPOINT")
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }
    payload = {"query": query, "variables": variables}
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.json(e.response.text)
        raise e

READ_QUERY = """
query {
  executesp_readData { id account_name classification partner_id_name Store Balance Year MonthName Month FinancialYearMonth last_modified_at last_modified_user }
}
"""
UPDATE_MUTATION = """
mutation updateBalance($id: Int!, $balance: Float, $last_modified_at: DateTime, $last_modified_user: String) {
  executesp_updateBalance(id: $id, balance: $balance, last_modified_at: $last_modified_at, last_modified_user: $last_modified_user) { rows_updated }
}
"""

# =============================
# HELPER FUNCTIONS
# =============================
def get_financial_year_range(df, year, start_month=4):
    """Get periods for a financial year (default: April to March)"""
    months = [(year, m) for m in range(start_month, 13)] + [(year + 1, m) for m in range(1, start_month)]
    
    periods = []
    for y, m in months:
        period_sort = f"{y}-{str(m).zfill(2)}"
        mask = (df['Year'] == y) & (df['Month'] == m)
        if mask.any():
            display = df.loc[mask, 'DisplayPeriod'].iloc[0]
            periods.append({'sort': period_sort, 'display': display})
    
    return periods

# =============================
# SESSION STATE INITIALIZATION
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logged_in_user = ""

# =============================
# APP FLOW: LOGGED OUT
# =============================
if not st.session_state.logged_in:
    # --- Sidebar Login ---
    with st.sidebar:
        st.markdown("<h2 style='color:#1E3A8A; font-weight:700;'>Secure Login</h2>", unsafe_allow_html=True)
        st.write("Sign in to access the dashboard.")
        with st.form("login_form"):
            username = st.text_input("Work Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")
            
            if submitted:
                if username == os.getenv("APP_USERNAME") and password == os.getenv("APP_PASSWORD"):
                    st.session_state.logged_in = True
                    st.session_state.logged_in_user = username
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")

    # --- Main Screen Features ---
    st.markdown("""
    <div class="hero-banner">
        <h1>Financial Intelligence Hub.</h1>
        <p>Your centralized dashboard for general ledger management, powerful financial reporting, and real-time data adjustments.</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("""
    <div class="feature-card">
        <div class="feature-icon">✨</div>
        <div class="feature-title">Real-time Integration</div>
        <div class="feature-text">Synchronize instantly with Microsoft Fabric for single-source-of-truth accuracy.</div>
    </div>
    """, unsafe_allow_html=True)
    c2.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Dynamic Insights</div>
        <div class="feature-text">Visualize P&L comparisons, custom periods, and hierarchical data instantly.</div>
    </div>
    """, unsafe_allow_html=True)
    c3.markdown("""
    <div class="feature-card">
        <div class="feature-icon">✏️</div>
        <div class="feature-title">Inline Editing</div>
        <div class="feature-text">Securely update balance adjustments with full audit tracking directly in the app.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()


# =============================
# DATA FETCHING (LOGGED IN ONLY)
# =============================
@st.cache_data(ttl=300)
def load_data():
    result = run_graphql(READ_QUERY)
    items = result.get("data", {}).get("executesp_readData", [])
    df = pd.DataFrame(items)
    if not df.empty:
        df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce').fillna(0.0)
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df['PeriodSort'] = df['Year'].astype(str) + "-" + df['Month'].astype(str).str.zfill(2)
        df['DisplayPeriod'] = df['MonthName'] + " " + df['Year'].astype(str)
    return df

with st.spinner("Synchronizing with Microsoft Fabric..."):
    if "original_df" not in st.session_state:
        raw_df = load_data()
        st.session_state.original_df = raw_df.copy()
        st.session_state.current_df = raw_df.copy()
        st.session_state.dirty = False

df = st.session_state.current_df.copy()
unique_periods = df[['PeriodSort', 'DisplayPeriod']].drop_duplicates().sort_values('PeriodSort', ascending=False)
period_list = unique_periods['DisplayPeriod'].tolist()
period_sort_to_display = dict(zip(unique_periods['PeriodSort'], unique_periods['DisplayPeriod']))

if df.empty:
    st.warning("No data retrieved from the database.")
    st.stop()


# =============================
# APP FLOW: LOGGED IN 
# =============================
# --- Dynamic Sidebar ---
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.logged_in_user.split('@')[0].title()}**")
    
    # Navigation replaces the tabs
    st.markdown("---")
    view_mode = st.radio("Navigation", ["📈 Financial Insights", "✏️ Ledger Editor"], label_visibility="collapsed")
    st.markdown("---")
    
    # Contextual Filters based on selected View Mode
    if view_mode == "📈 Financial Insights":
        st.markdown("### 📊 Report Filters")
        
        # Date Range Selection Type
        date_range_type = st.radio(
            "Select Range Type",
            ["📅 Single/Multiple Months", "📆 Financial Year"],
            horizontal=True,
            key="date_range_type"
        )
        
        if date_range_type == "📅 Single/Multiple Months":
            base_period = st.selectbox("📅 Base Period", period_list, key="rep_base_period")
            num_comparisons = st.number_input("📉 Previous Periods", min_value=0, max_value=12, value=3, step=1)
            
            # Get selected periods based on base and count
            base_idx = period_list.index(base_period)
            selected_periods = period_list[base_idx : min(base_idx + num_comparisons + 1, len(period_list))]
            
        else:  # Financial Year
            # Get available years
            available_years = sorted(df['Year'].dropna().unique(), reverse=True)
            selected_year = st.selectbox("📆 Financial Year (Apr-Mar)", available_years, key="fy_year")
            
            # Get financial year periods
            fy_periods = get_financial_year_range(df, selected_year, start_month=4)
            if fy_periods:
                selected_periods = [p['display'] for p in fy_periods]
                st.info(f"Showing {len(selected_periods)} periods: {fy_periods[0]['display']} to {fy_periods[-1]['display']}")
            else:
                selected_periods = []
                st.warning("No data available for the selected financial year")
        
        store_filter = st.selectbox("🏢 Store Filter", ["All"] + sorted(list(df['Store'].dropna().astype(str).unique())), key="rep_store")
        
    elif view_mode == "✏️ Ledger Editor":
        st.markdown("### ✏️ Editor Filters")
        edit_period = st.selectbox("📅 Period", period_list, key="edit_period")
        
        # Cascade data based on period
        e_filtered = df[df['DisplayPeriod'] == edit_period]
        
        e_store = st.selectbox("🏢 Store", ["All"] + sorted(list(df['Store'].dropna().astype(str).unique())), key="e_store")
        if e_store != "All": e_filtered = e_filtered[e_filtered['Store'] == e_store]
            
        e_class = st.selectbox("📂 Class", ["All"] + sorted(list(e_filtered['classification'].dropna().astype(str).unique())), key="e_class")
        if e_class != "All": e_filtered = e_filtered[e_filtered['classification'] == e_class]
            
        e_account = st.selectbox("📝 Account", ["All"] + sorted(list(e_filtered['account_name'].dropna().astype(str).unique())), key="e_account")
        if e_account != "All": e_filtered = e_filtered[e_filtered['account_name'] == e_account]

        e_partner = st.selectbox("🤝 Partner", ["All"] + sorted(list(e_filtered['partner_id_name'].dropna().astype(str).unique())), key="e_partner")
        if e_partner != "All": e_filtered = e_filtered[e_filtered['partner_id_name'] == e_partner]

    # Logout at the bottom of the sidebar
    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.logged_in_user = ""
        st.cache_data.clear()
        st.rerun()

# --- Main Content Area ---
st.markdown(f'<div class="main-header">💠 {view_mode.split(" ", 1)[1]}</div>', unsafe_allow_html=True)

# -----------------------------------
# VIEW 1: FINANCIAL INSIGHTS
# -----------------------------------
if view_mode == "📈 Financial Insights":
    
    # Get selected periods based on date range type (already set in sidebar)
    if date_range_type == "📅 Single/Multiple Months":
        # selected_periods already set in sidebar
        pass
    else:  # Financial Year
        # selected_periods already set in sidebar
        pass
    
    report_df = df[df['DisplayPeriod'].isin(selected_periods)].copy()
    if store_filter != "All":
        report_df = report_df[report_df['Store'] == store_filter]

    if report_df.empty:
        st.info("ℹ️ No data available for the selected filters.")
    else:
        # Metrics Calculation (using latest period for KPIs)
        latest_period = selected_periods[0] if selected_periods else None
        base_data = report_df[report_df['DisplayPeriod'] == latest_period] if latest_period else pd.DataFrame()
        
        revenue_classes = ['Income', 'Other Income']
        total_revenue = base_data[base_data['classification'].isin(revenue_classes)]['Balance'].sum()
        total_op_expenses = base_data[~base_data['classification'].isin(revenue_classes)]['Balance'].sum()
        net_profit = total_revenue - total_op_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue != 0 else 0

        # Beautiful Custom KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""
        <div class="kpi-container bg-revenue">
            <div class="kpi-title">Total Revenue ({latest_period})</div>
            <div class="kpi-value">₹{total_revenue:,.0f}</div>
            <div><span class="kpi-sub">100% of Top Line</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        c2.markdown(f"""
        <div class="kpi-container bg-expense">
            <div class="kpi-title">Operating Expenses ({latest_period})</div>
            <div class="kpi-value">₹{total_op_expenses:,.0f}</div>
            <div><span class="kpi-sub">{abs((total_op_expenses/total_revenue*100) if total_revenue!=0 else 0):.1f}% of Rev</span></div>
        </div>
        """, unsafe_allow_html=True)

        c3.markdown(f"""
        <div class="kpi-container bg-profit">
            <div class="kpi-title">Net Profit ({latest_period})</div>
            <div class="kpi-value">₹{net_profit:,.0f}</div>
            <div><span class="kpi-sub">Bottom Line</span></div>
        </div>
        """, unsafe_allow_html=True)

        c4.markdown(f"""
        <div class="kpi-container bg-margin">
            <div class="kpi-title">Net Margin ({latest_period})</div>
            <div class="kpi-value">{profit_margin:.1f}%</div>
            <div><span class="kpi-sub">Profitability</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.write("<br>", unsafe_allow_html=True)

        # Plotly Area Chart
        period_totals = report_df.groupby('DisplayPeriod')['Balance'].sum().reset_index()
        period_totals['SortCol'] = period_totals['DisplayPeriod'].apply(
            lambda x: list(selected_periods).index(x) if x in selected_periods else 999
        )
        period_totals = period_totals.sort_values('SortCol', ascending=True)
        
        fig = px.area(period_totals, x='DisplayPeriod', y='Balance', 
                      title='<b>Net Balance Trend Over Selected Periods</b>',
                      markers=True, color_discrete_sequence=['#3B82F6'])
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(gridcolor='#E2E8F0', title=''),
            xaxis=dict(title='')
        )
        fig.update_traces(fillcolor='rgba(59, 130, 246, 0.2)', line=dict(width=3, shape='spline'))
        st.plotly_chart(fig, use_container_width=True)

        # --- BUILD HIERARCHICAL DATAFRAME ---
        def build_hierarchical_report(data, periods):
            rows = []
            classifications = sorted(data['classification'].dropna().unique())
            for classification in classifications:
                class_df = data[data['classification'] == classification]
                class_totals = class_df.groupby('DisplayPeriod')['Balance'].sum()
                class_row = {'Account Name': f"📂 {classification}", 'Type': 'Classification'}
                for p in periods:
                    class_row[p] = class_totals.get(p, 0.0)
                rows.append(class_row)
                
                acc_grouped = class_df.groupby(['account_name', 'DisplayPeriod'])['Balance'].sum().unstack(fill_value=0.0)
                for acc_name, acc_row_data in acc_grouped.iterrows():
                    acc_row = {'Account Name': f"    ▫️ {acc_name}", 'Type': 'Account'}
                    for p in periods:
                        acc_row[p] = acc_row_data.get(p, 0.0)
                    rows.append(acc_row)
            return pd.DataFrame(rows)

        hierarchical_df = build_hierarchical_report(report_df, selected_periods)

        def style_financial_report(row):
            styles = [''] * len(row)
            if row['Type'] == 'Classification':
                styles = ['background-color: #F1F5F9; font-weight: 700; color: #1E293B;'] * len(row)
            
            for idx, col in enumerate(hierarchical_df.columns):
                if col in selected_periods:
                    val = row[col]
                    if isinstance(val, (int, float)):
                        if val < 0:
                            styles[idx] = styles[idx] + '; color: #E11D48; font-weight: 600;'
                        elif val > 0:
                            styles[idx] = styles[idx] + '; color: #059669;'
            return styles

        format_dict = {col: "₹{:,.2f}" for col in selected_periods}
        
        styled_df = hierarchical_df.style\
            .apply(style_financial_report, axis=1)\
            .format(format_dict)\
            .set_properties(**{
                'padding': '12px 15px',
                'border-bottom': '1px solid #E2E8F0',
                'font-size': '14px'
            })

        st.markdown("### 📋 Detailed Statement")
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            height=600,
            hide_index=True,
            column_config={"Type": None}
        )

# -----------------------------------
# VIEW 2: LEDGER EDITOR
# -----------------------------------
elif view_mode == "✏️ Ledger Editor":
    st.write("Double-click the **Balance** cell of any record below to make adjustments. Save changes to commit to Fabric.")
    
    if st.session_state.dirty:
        st.info("⚠️ You have pending edits. Click 'Save to Fabric' below to commit them.")

    base_display_cols = ['id', 'Store', 'classification', 'account_name', 'partner_id_name', 'Balance']
    editor_display_df = e_filtered[base_display_cols].copy()

    if editor_display_df.empty:
        st.warning("No records found for the filters selected in the sidebar.")
    else:
        st.markdown(f"<span style='color:#64748B; font-weight:500;'>{len(editor_display_df)} records ready for editing</span>", unsafe_allow_html=True)
        
        editor_df = st.data_editor(
            editor_display_df,
            key="editor",
            use_container_width=True,
            num_rows="fixed",
            disabled=[c for c in base_display_cols if c != 'Balance'],
            column_config={
                "id": None, # Hides the ID column entirely from the UI, but keeps it in memory
                "Balance": st.column_config.NumberColumn(
                    "Balance (₹)",
                    help="Double click to edit",
                    format="₹%.2f",
                    step=0.01,
                    required=True
                ),
                "Store": st.column_config.TextColumn("Store", disabled=True),
                "classification": st.column_config.TextColumn("Classification", disabled=True),
                "account_name": st.column_config.TextColumn("Account", disabled=True),
                "partner_id_name": st.column_config.TextColumn("Partner", disabled=True)
            }
        )

        changed_mask = editor_df['Balance'] != editor_display_df['Balance']
        if changed_mask.any():
            st.session_state.dirty = True
            for index in editor_df[changed_mask].index:
                row_id = editor_df.loc[index, 'id'] # ID is still accessible here!
                st.session_state.current_df.loc[
                    st.session_state.current_df['id'] == row_id, 'Balance'
                ] = editor_df.loc[index, 'Balance']

    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 2, 2])
    with col2:
        if st.button("🗑️ Discard", use_container_width=True, disabled=not st.session_state.dirty):
            st.session_state.current_df = st.session_state.original_df.copy()
            st.session_state.dirty = False
            st.rerun()
    with col3:
        if st.button("💾 Save to Fabric", use_container_width=True, disabled=not st.session_state.dirty, type="primary"):
            baseline_df = st.session_state.original_df
            working_df = st.session_state.current_df
            delta_rows = working_df[working_df['Balance'] != baseline_df['Balance']]
            
            if not delta_rows.empty:
                with st.spinner(f"Writing {len(delta_rows)} updates..."):
                    s_count, e_count = 0, 0
                    p_bar = st.progress(0)
                    for idx, (_, row) in enumerate(delta_rows.iterrows()):
                        f_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        vars = {
                            "id": int(row["id"]),
                            "balance": float(row["Balance"]) if pd.notnull(row["Balance"]) else 0.0,
                            "last_modified_at": f_time,
                            "last_modified_user": st.session_state.logged_in_user
                        }
                        try:
                            res = run_graphql(UPDATE_MUTATION, vars)
                            if "errors" in res: e_count += 1
                            else:
                                s_count += 1
                                st.session_state.current_df.loc[
                                    st.session_state.current_df['id'] == row['id'], 
                                    ['last_modified_at', 'last_modified_user']
                                ] = [f_time, st.session_state.logged_in_user]
                        except: e_count += 1
                        p_bar.progress((idx + 1) / len(delta_rows))
                    
                    if e_count == 0:
                        st.session_state.original_df = st.session_state.current_df.copy()
                        st.session_state.dirty = False
                        load_data.clear()
                        st.success(f"✅ {s_count} changes saved!")
                        st.balloons()
                        st.rerun()
                    elif s_count > 0:
                        st.warning(f"⚠️ {s_count} succeeded, {e_count} failed.")
                        st.session_state.original_df = st.session_state.current_df.copy()
                        st.session_state.dirty = False
                        load_data.clear()
                    else: st.error("❌ All updates failed.")
