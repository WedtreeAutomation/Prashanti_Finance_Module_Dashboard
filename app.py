import streamlit as st
import pandas as pd
import requests
import os
import io
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
# CUSTOM CSS - CLEAN LIGHT THEME
# =============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background-color: #F0F4F8; }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F2044 0%, #1A3A6B 60%, #1D5FAA 100%);
        padding: 5rem 3rem; border-radius: 20px; color: white;
        box-shadow: 0 20px 60px rgba(15, 32, 68, 0.3);
        margin-bottom: 2rem; position: relative; overflow: hidden;
    }
    .hero-banner::before {
        content: ''; position: absolute; top: -50%; right: -10%;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, transparent 70%); border-radius: 50%;
    }
    .hero-banner h1 { color: white; font-size: 3.2rem; font-weight: 700; line-height: 1.15; margin-bottom: 1rem; letter-spacing: -0.5px; }
    .hero-banner p { font-size: 1.15rem; opacity: 0.8; color: #B8D4F5; max-width: 600px; }

    /* Feature Cards */
    .feature-card {
        background: white; padding: 2rem; border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06); height: 100%;
        border: 1px solid #E8EDF4; transition: transform 0.2s, box-shadow 0.2s;
    }
    .feature-card:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.1); }
    .feature-icon { font-size: 2rem; margin-bottom: 1rem; }
    .feature-title { font-weight: 700; color: #0F2044; margin-bottom: 0.5rem; font-size: 1.05rem; }
    .feature-text { color: #64748B; font-size: 0.9rem; line-height: 1.6; }

    /* Main Header */
    .main-header { font-size: 1.9rem; font-weight: 700; color: #0F2044; margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 2px solid #DCE5F0; letter-spacing: -0.3px; }

    /* KPI Cards */
    .kpi-container { padding: 1rem 1.2rem; border-radius: 16px; color: white; box-shadow: 0 8px 24px rgba(0,0,0,0.12); transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1); }
    .kpi-container:hover { transform: translateY(-4px); }
    .kpi-title { font-size: 0.7rem; font-weight: 600; opacity: 0.85; margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap; }
    .kpi-value { font-size: 1.2rem; font-weight: 700; line-height: 1.1; margin-bottom: 0.4rem; font-family: 'DM Mono', monospace; white-space: nowrap; }
    .kpi-sub { font-size: 0.68rem; font-weight: 500; background: rgba(255,255,255,0.18); padding: 2px 8px; border-radius: 20px; display: inline-block; }

    .bg-revenue { background: linear-gradient(135deg, #0AB370 0%, #059669 100%); }
    .bg-expense { background: linear-gradient(135deg, #F43F5E 0%, #BE123C 100%); }
    .bg-profit { background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); }
    .bg-margin { background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%); }

    /* Compact Headers */
    .compact-header { font-size: 11px; font-weight: 600; color: #64748B; text-align: right; white-space: nowrap; }
    .compact-header-left { font-size: 11px; font-weight: 600; color: #64748B; text-align: left; }

    /* Sidebar Theme */
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E8EDF4; }
    section[data-testid="stSidebar"] .stApp { background-color: transparent; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #475569 !important; }
    
    section[data-testid="stSidebar"] div[data-baseweb="select"] *,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] div[class*="stSelectbox"] *,
    section[data-testid="stSidebar"] div[class*="stNumberInput"] * { color: initial !important; }
    
    section[data-testid="stSidebar"] label p { color: #334155 !important; font-weight: 600; font-size: 0.85rem; }
    section[data-testid="stSidebar"] h2 { color: #0F2044 !important; font-weight: 700; font-size: 1.3rem; letter-spacing: -0.3px; border-bottom: 2px solid #E8EDF4; padding-bottom: 10px; margin-bottom: 10px; }
    section[data-testid="stSidebar"] hr { border-color: #E8EDF4; margin: 15px 0; }

    section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #0F2044 0%, #1D5FAA 100%); color: white !important; border: none; border-radius: 8px; font-weight: 600; transition: all 0.2s;
    }
    section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"]:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(15, 32, 68, 0.2); }
    section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-secondary"] { background: #F8FAFC; color: #0F2044 !important; border: 1px solid #CBD5E1; border-radius: 8px; font-weight: 600; }

    .sidebar-user-info {
        background: #F8FAFC; padding: 12px 15px; border-radius: 12px; margin-bottom: 15px;
        border-left: 4px solid #1D5FAA; border-top: 1px solid #E8EDF4; border-right: 1px solid #E8EDF4; border-bottom: 1px solid #E8EDF4;
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
    months = [(year, m) for m in range(start_month, 13)] + [(year + 1, m) for m in range(1, start_month)]
    periods = []
    for y, m in months:
        period_sort = f"{y}-{str(m).zfill(2)}"
        mask = (df['Year'] == y) & (df['Month'] == m)
        if mask.any():
            display = df.loc[mask, 'DisplayPeriod'].iloc[0]
            periods.append({'sort': period_sort, 'display': display})
    return periods

def calculate_profit_metrics(df, periods, revenue_classes):
    results = []
    for period in periods:
        period_data = df[df['DisplayPeriod'] == period]
        revenue = period_data[period_data['classification'].isin(revenue_classes)]['Balance'].sum()
        expenses = period_data[~period_data['classification'].isin(revenue_classes)]['Balance'].sum()
        profit = revenue - expenses
        results.append({
            'DisplayPeriod': period,
            'Revenue': revenue,
            'Expenses': expenses,
            'Profit': profit,
            'Margin': (profit / revenue * 100) if revenue != 0 else 0
        })
    return pd.DataFrame(results)

def fmt_currency(val):
    if pd.isna(val) or val == 0: return "₹0"
    return f"₹{val:,.0f}"

# =============================
# HIERARCHICAL DATA BUILDER
# =============================
def build_hierarchy_data(report_df, periods):
    hierarchy = {}
    for classification in sorted(report_df['classification'].dropna().unique()):
        cls_df = report_df[report_df['classification'] == classification]
        cls_totals = {}
        for p in periods:
            cls_totals[p] = cls_df[cls_df['DisplayPeriod'] == p]['Balance'].sum()
        
        accounts = {}
        for account in sorted(cls_df['account_name'].dropna().unique()):
            acc_df = cls_df[cls_df['account_name'] == account]
            acc_totals = {}
            for p in periods:
                acc_totals[p] = acc_df[acc_df['DisplayPeriod'] == p]['Balance'].sum()
            
            partners = {}
            for partner in sorted(acc_df['partner_id_name'].dropna().unique()):
                prt_df = acc_df[acc_df['partner_id_name'] == partner]
                prt_totals = {}
                for p in periods:
                    prt_totals[p] = prt_df[prt_df['DisplayPeriod'] == p]['Balance'].sum()
                partners[partner] = prt_totals
            
            accounts[account] = {'totals': acc_totals, 'partners': partners}
        
        hierarchy[classification] = {'totals': cls_totals, 'accounts': accounts}
    return hierarchy

# =============================
# EXCEL EXPORT WITH NATIVE GROUPING
# =============================
def build_excel_report(hierarchy, periods, store_filter="All", expand_all=False, open_classifications=None, open_accounts=None):
    if open_classifications is None: open_classifications = set()
    if open_accounts is None: open_accounts = set()

    import openpyxl
    from openpyxl.styles import (PatternFill, Font, Alignment, Border, Side)
    from openpyxl.utils import get_column_letter
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "P&L Statement"

    # Crucial for Excel grouping: Summary rows are ABOVE detail rows
    ws.sheet_properties.outlinePr.summaryBelow = False
    
    DARK_BLUE, MID_BLUE, LIGHT_BLUE, WHITE = "0F2044", "1A3A6B", "EEF2F9", "FFFFFF"
    GREEN, RED, GREY = "059669", "E11D48", "64748B"
    
    def make_fill(hex_color): return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")
    hair_border = Border(bottom=Side(style='hair', color='E2E8F0'))
    
    # --- Title Block ---
    ws.merge_cells(f"A1:{get_column_letter(len(periods) + 3)}1")
    title_cell = ws["A1"]
    title_cell.value = "Profit & Loss Statement"
    title_cell.font = Font(name="Calibri", bold=True, size=14, color=WHITE)
    title_cell.fill = make_fill(DARK_BLUE)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30
    
    ws.merge_cells(f"A2:{get_column_letter(len(periods) + 3)}2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Store: {store_filter}  |  Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}"
    sub_cell.font = Font(name="Calibri", size=9, color="B8D4F5")
    sub_cell.fill = make_fill(MID_BLUE)
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 6
    
    # --- Headers ---
    header_row = 4
    headers = ["Account Hierarchy"] + list(periods) + ["Total"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = Font(name="Calibri", bold=True, size=9, color=WHITE)
        cell.fill = make_fill(DARK_BLUE)
        cell.alignment = Alignment(horizontal="right" if col_idx > 1 else "left", vertical="center", wrap_text=False)
        cell.border = Border(bottom=Side(style='medium', color='FFFFFF'))
    ws.row_dimensions[header_row].height = 24
    
    ws.column_dimensions['A'].width = 38
    for col_idx in range(2, len(periods) + 2): ws.column_dimensions[get_column_letter(col_idx)].width = 15
    ws.column_dimensions[get_column_letter(len(periods) + 2)].width = 15
    
    # --- Data Population with Outline Grouping ---
    current_row = header_row + 1
    
    for cls_name, cls_data in hierarchy.items():
        cls_key = f"cls_{cls_name}"
        is_cls_open = expand_all or (cls_key in open_classifications)
        cls_total = sum(cls_data['totals'].values())
        
        # 1. Classification (Level 0 summary - no outline level)
        cls_cell = ws.cell(row=current_row, column=1, value=f"  {cls_name}")
        cls_cell.font = Font(name="Calibri", bold=True, size=10, color=DARK_BLUE)
        cls_cell.fill = make_fill(LIGHT_BLUE)
        cls_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        cls_cell.border = Border(top=Side(style='thin', color='CBD5E1'), bottom=Side(style='thin', color='CBD5E1'))
        
        for col_idx, p in enumerate(periods, 2):
            v = cls_data['totals'].get(p, 0)
            cell = ws.cell(row=current_row, column=col_idx, value=v)
            cell.number_format = '#,##0'
            cell.font = Font(name="Calibri", bold=True, size=9, color=GREEN if v > 0 else RED if v < 0 else GREY)
            cell.fill = make_fill(LIGHT_BLUE)
            cell.alignment = Alignment(horizontal="right", vertical="center")
            cell.border = Border(top=Side(style='thin', color='CBD5E1'), bottom=Side(style='thin', color='CBD5E1'))
        
        total_cell = ws.cell(row=current_row, column=len(periods) + 2, value=cls_total)
        total_cell.number_format = '#,##0'
        total_cell.font = Font(name="Calibri", bold=True, size=9, color=GREEN if cls_total > 0 else RED if cls_total < 0 else GREY)
        total_cell.fill = make_fill(LIGHT_BLUE)
        total_cell.alignment = Alignment(horizontal="right", vertical="center")
        total_cell.border = Border(top=Side(style='thin', color='CBD5E1'), bottom=Side(style='thin', color='CBD5E1'))
        ws.row_dimensions[current_row].height = 20
        current_row += 1
        
        for acc_name, acc_data in cls_data['accounts'].items():
            acc_key = f"acc_{cls_name}__{acc_name}"
            is_acc_open = expand_all or (acc_key in open_accounts)
            acc_total = sum(acc_data['totals'].values())
            
            # 2. Account (Level 1 details inside Classification)
            acc_cell = ws.cell(row=current_row, column=1, value=f"      {acc_name}")
            acc_cell.font = Font(name="Calibri", bold=True, size=9, color="334155")
            acc_cell.fill = make_fill(WHITE)
            acc_cell.alignment = Alignment(horizontal="left", vertical="center", indent=3)
            acc_cell.border = hair_border
            
            for col_idx, p in enumerate(periods, 2):
                v = acc_data['totals'].get(p, 0)
                cell = ws.cell(row=current_row, column=col_idx, value=v)
                cell.number_format = '#,##0'
                cell.font = Font(name="Calibri", bold=True, size=8, color=GREEN if v > 0 else RED if v < 0 else GREY)
                cell.fill = make_fill(WHITE)
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.border = hair_border
            
            acc_total_cell = ws.cell(row=current_row, column=len(periods) + 2, value=acc_total)
            acc_total_cell.number_format = '#,##0'
            acc_total_cell.font = Font(name="Calibri", bold=True, size=8, color=GREEN if acc_total > 0 else RED if acc_total < 0 else GREY)
            acc_total_cell.fill = make_fill(WHITE)
            acc_total_cell.alignment = Alignment(horizontal="right", vertical="center")
            acc_total_cell.border = hair_border
            
            # ** EXCEL NATIVE GROUPING LOGIC **
            ws.row_dimensions[current_row].outline_level = 1
            if not is_cls_open:
                ws.row_dimensions[current_row].hidden = True
                
            ws.row_dimensions[current_row].height = 18
            current_row += 1
            
            for partner_name, prt_totals in acc_data['partners'].items():
                prt_total = sum(prt_totals.values())
                
                # 3. Partner (Level 2 details inside Account)
                prt_cell = ws.cell(row=current_row, column=1, value=f"            · {partner_name}")
                prt_cell.font = Font(name="Calibri", size=8, color=GREY)
                prt_cell.fill = make_fill(WHITE)
                prt_cell.alignment = Alignment(horizontal="left", vertical="center", indent=5)
                prt_cell.border = hair_border
                
                for col_idx, p in enumerate(periods, 2):
                    v = prt_totals.get(p, 0)
                    cell = ws.cell(row=current_row, column=col_idx, value=v)
                    cell.number_format = '#,##0'
                    cell.font = Font(name="Calibri", size=8, color=GREEN if v > 0 else RED if v < 0 else GREY)
                    cell.fill = make_fill(WHITE)
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.border = hair_border
                
                prt_total_cell = ws.cell(row=current_row, column=len(periods) + 2, value=prt_total)
                prt_total_cell.number_format = '#,##0'
                prt_total_cell.font = Font(name="Calibri", size=8, color=GREEN if prt_total > 0 else RED if prt_total < 0 else GREY)
                prt_total_cell.fill = make_fill(WHITE)
                prt_total_cell.alignment = Alignment(horizontal="right", vertical="center")
                prt_total_cell.border = hair_border
                
                # ** EXCEL NATIVE GROUPING LOGIC **
                ws.row_dimensions[current_row].outline_level = 2
                if not is_cls_open or not is_acc_open:
                    ws.row_dimensions[current_row].hidden = True
                    
                ws.row_dimensions[current_row].height = 16
                current_row += 1
    
    # Grand Total
    grand_totals = {p: sum(cls_data['totals'].get(p, 0) for cls_data in hierarchy.values()) for p in periods}
    grand_total = sum(grand_totals.values())
    
    gt_cell = ws.cell(row=current_row, column=1, value="  GRAND TOTAL")
    gt_cell.font = Font(name="Calibri", bold=True, size=11, color=WHITE)
    gt_cell.fill = make_fill(DARK_BLUE)
    gt_cell.alignment = Alignment(horizontal="left", vertical="center")
    
    for col_idx, p in enumerate(periods, 2):
        cell = ws.cell(row=current_row, column=col_idx, value=grand_totals[p])
        cell.number_format = '#,##0'
        cell.font = Font(name="Calibri", bold=True, size=10, color=WHITE)
        cell.fill = make_fill(DARK_BLUE)
        cell.alignment = Alignment(horizontal="right", vertical="center")
    
    gt_total = ws.cell(row=current_row, column=len(periods) + 2, value=grand_total)
    gt_total.number_format = '#,##0'
    gt_total.font = Font(name="Calibri", bold=True, size=10, color=WHITE)
    gt_total.fill = make_fill(DARK_BLUE)
    gt_total.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[current_row].height = 24
    
    ws.freeze_panes = "B5"
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

# =============================
# PERSISTENT SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    # Read query parameter to persist auth state across browser refreshes
    if st.query_params.get("auth") == "active":
        st.session_state.logged_in = True
        st.session_state.logged_in_user = st.query_params.get("user", "")
    else:
        st.session_state.logged_in = False
        st.session_state.logged_in_user = ""

if "open_classifications" not in st.session_state: st.session_state.open_classifications = set()
if "open_accounts" not in st.session_state: st.session_state.open_accounts = set()

# URL PARAM HANDLING FOR TREE TOGGLES
params = st.query_params
if "toggle_cls" in params:
    key = params["toggle_cls"]
    if key in st.session_state.open_classifications:
        st.session_state.open_classifications.discard(key)
        st.session_state.open_accounts = {a for a in st.session_state.open_accounts if not a.startswith(f"acc_{key.replace('cls_', '')}__")}
    else:
        st.session_state.open_classifications.add(key)
    # Remove toggle param specifically to avoid clearing the active auth state
    del st.query_params["toggle_cls"]
    st.rerun()

if "toggle_acc" in params:
    key = params["toggle_acc"]
    if key in st.session_state.open_accounts: st.session_state.open_accounts.discard(key)
    else: st.session_state.open_accounts.add(key)
    del st.query_params["toggle_acc"]
    st.rerun()

# =============================
# APP FLOW: LOGGED OUT
# =============================
if not st.session_state.logged_in:
    with st.sidebar:
        st.markdown("<h2 style='color:#0F2044; font-weight:700;'>Secure Login</h2>", unsafe_allow_html=True)
        st.write("Sign in to access the dashboard.")
        with st.form("login_form"):
            username = st.text_input("Work Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")
            if submitted:
                if username == os.getenv("APP_USERNAME") and password == os.getenv("APP_PASSWORD"):
                    st.session_state.logged_in = True
                    st.session_state.logged_in_user = username
                    # Write token to URL to survive page refresh
                    st.query_params["auth"] = "active"
                    st.query_params["user"] = username
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    st.markdown("""
    <div class="hero-banner">
        <h1>Financial Intelligence Hub.</h1>
        <p>Your centralized dashboard for general ledger management, powerful financial reporting, and real-time data adjustments.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    features = [
        ("✨", "Real-time Integration", "Synchronize instantly with Microsoft Fabric for single-source-of-truth accuracy."),
        ("📊", "Dynamic Insights", "Visualize P&L comparisons, custom periods, and hierarchical data instantly."),
        ("✏️", "Inline Editing", "Securely update balance adjustments with full audit tracking directly in the app.")
    ]
    for col, (icon, title, text) in zip(cols, features):
        col.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# =============================
# DATA FETCHING
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

if df.empty:
    st.warning("No data retrieved from the database.")
    st.stop()

REVENUE_CLASSES = ['Income', 'Other Income']

# =============================
# SIDEBAR NAVIGATION
# =============================
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-user-info">
        <p style='margin:0; font-size:11px; color:#64748B;'>SIGNED IN AS</p>
        <p style='margin:0; font-weight:700; color:#0F2044;'>👤 {st.session_state.logged_in_user.split('@')[0].title()}</p>
    </div>
    """, unsafe_allow_html=True)

    view_mode = st.radio("Navigation", ["📈 Financial Insights", "✏️ Ledger Editor"], label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    if view_mode == "📈 Financial Insights":
        st.markdown("<p style='color:#0F2044 !important; font-weight:600; font-size:1rem;'>📊 Report Filters</p>", unsafe_allow_html=True)
        date_range_type = st.radio("Range Type", ["📅 Single/Multiple Months", "📆 Financial Year"], horizontal=True)

        if date_range_type == "📅 Single/Multiple Months":
            base_period = st.selectbox("Base Period", period_list, key="rep_base_period")
            num_comparisons = st.number_input("Previous Periods", min_value=0, max_value=12, value=3)
            base_idx = period_list.index(base_period)
            selected_periods = period_list[base_idx: min(base_idx + num_comparisons + 1, len(period_list))]
        else:
            available_years = sorted(df['Year'].dropna().unique(), reverse=True)
            selected_year = st.selectbox("Financial Year (Apr–Mar)", available_years)
            fy_periods = get_financial_year_range(df, selected_year, start_month=4)
            if fy_periods:
                selected_periods = [p['display'] for p in fy_periods]
                st.info(f"{len(selected_periods)} periods: {fy_periods[0]['display']} → {fy_periods[-1]['display']}")
            else:
                selected_periods = []

        store_filter = st.selectbox("🏢 Store", ["All"] + sorted(df['Store'].dropna().astype(str).unique()))

    elif view_mode == "✏️ Ledger Editor":
        st.markdown("<p style='color:#0F2044 !important; font-weight:600; font-size:1rem;'>✏️ Editor Filters</p>", unsafe_allow_html=True)
        edit_period = st.selectbox("Period", period_list)
        e_filtered = df[df['DisplayPeriod'] == edit_period]
        e_store = st.selectbox("Store", ["All"] + sorted(df['Store'].dropna().astype(str).unique()))
        if e_store != "All": e_filtered = e_filtered[e_filtered['Store'] == e_store]
        e_class = st.selectbox("Class", ["All"] + sorted(e_filtered['classification'].dropna().astype(str).unique()))
        if e_class != "All": e_filtered = e_filtered[e_filtered['classification'] == e_class]
        e_account = st.selectbox("Account", ["All"] + sorted(e_filtered['account_name'].dropna().astype(str).unique()))
        if e_account != "All": e_filtered = e_filtered[e_filtered['account_name'] == e_account]
        e_partner = st.selectbox("Partner", ["All"] + sorted(e_filtered['partner_id_name'].dropna().astype(str).unique()))
        if e_partner != "All": e_filtered = e_filtered[e_filtered['partner_id_name'] == e_partner]

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.logged_in_user = ""
        st.query_params.clear() # Clears URL auth state token
        st.cache_data.clear()
        st.rerun()

# =============================
# MAIN CONTENT
# =============================
st.markdown(f'<div class="main-header">💠 {view_mode.split(" ", 1)[1]}</div>', unsafe_allow_html=True)

# ===========================
# FINANCIAL INSIGHTS VIEW
# ===========================
if view_mode == "📈 Financial Insights":
    if not selected_periods:
        st.info("ℹ️ No periods selected or available.")
        st.stop()

    report_df = df[df['DisplayPeriod'].isin(selected_periods)].copy()
    if store_filter != "All": report_df = report_df[report_df['Store'] == store_filter]

    if report_df.empty:
        st.info("ℹ️ No data available for the selected filters.")
        st.stop()

    latest_period = selected_periods[0]
    latest_data = report_df[report_df['DisplayPeriod'] == latest_period]
    total_revenue = latest_data[latest_data['classification'].isin(REVENUE_CLASSES)]['Balance'].sum()
    total_expenses = latest_data[~latest_data['classification'].isin(REVENUE_CLASSES)]['Balance'].sum()
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue != 0 else 0

    cols = st.columns(4)
    kpi_configs = [
        (cols[0], "bg-revenue", "REVENUE", fmt_currency(total_revenue), f"{abs((total_expenses/total_revenue*100) if total_revenue!=0 else 0):.1f}% OPEX"),
        (cols[1], "bg-expense", "EXPENSES", fmt_currency(total_expenses), f"{abs((total_expenses/total_revenue*100) if total_revenue!=0 else 0):.1f}% of Rev"),
        (cols[2], "bg-profit", "NET PROFIT", fmt_currency(net_profit), f"{abs((total_expenses/total_revenue*100) if total_revenue!=0 else 0):.1f}% Margin"),
        (cols[3], "bg-margin", "MARGIN", f"{profit_margin:.1f}%", f"{latest_period[:3]}")
    ]
    for col, bg_class, title, value, sub in kpi_configs:
        col.markdown(f"""
        <div class="kpi-container {bg_class}">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div><span class="kpi-sub">{sub}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)

    profit_df = calculate_profit_metrics(report_df, selected_periods, REVENUE_CLASSES)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=profit_df['DisplayPeriod'], y=profit_df['Revenue'], name='Revenue', marker_color='#0AB370', opacity=0.8))
    fig.add_trace(go.Bar(x=profit_df['DisplayPeriod'], y=profit_df['Expenses'], name='Expenses', marker_color='#F43F5E', opacity=0.8))
    fig.add_trace(go.Scatter(x=profit_df['DisplayPeriod'], y=profit_df['Profit'], mode='lines+markers', name='Net Profit', line=dict(color='#2563EB', width=3, shape='spline'), marker=dict(size=8, color='#1D4ED8'), yaxis='y'))
    fig.update_layout(title=dict(text='<b>Revenue, Expenses & Net Profit</b>', font=dict(size=15, color='#0F2044')), barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=40), yaxis=dict(gridcolor='#E2E8F0', title='Amount (₹)', tickformat='₹,.0f'), xaxis=dict(showline=True, linecolor='#CBD5E1', tickfont=dict(size=10)), hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0.9)', font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    hierarchy = build_hierarchy_data(report_df, selected_periods)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("### 📋 P&L Statement")
    with col2:
        export_col1, export_col2, export_col3 = st.columns([1, 1, 1])
        with export_col1:
            if st.button("⊞ Expand All", use_container_width=True):
                for cls_name in hierarchy.keys():
                    st.session_state.open_classifications.add(f"cls_{cls_name}")
                    for acc_name in hierarchy[cls_name]['accounts'].keys():
                        st.session_state.open_accounts.add(f"acc_{cls_name}__{acc_name}")
                st.rerun()
        with export_col2:
            if st.button("Collapse All", use_container_width=True):
                st.session_state.open_classifications.clear()
                st.session_state.open_accounts.clear()
                st.rerun()
        with export_col3:
            expand_all = len(st.session_state.open_classifications) > 0 or len(st.session_state.open_accounts) > 0
            # Pass UI state directly into the Excel builder
            excel_bytes = build_excel_report(
                hierarchy, selected_periods, store_filter, 
                expand_all=expand_all,
                open_classifications=st.session_state.open_classifications,
                open_accounts=st.session_state.open_accounts
            )
            st.download_button(
                label="📥 Export", data=excel_bytes,
                file_name=f"PL_Report_{store_filter}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary"
            )

    st.markdown("<p style='color:#64748B; font-size:0.8rem; margin-bottom:0.5rem;'>Click on Classification rows to expand accounts. Click on Account rows to expand partners.</p>", unsafe_allow_html=True)

    num_cols = len(selected_periods) + 2 
    col_widths = [3] + [1] * len(selected_periods) + [1]
    
    header_cols = st.columns(col_widths)
    header_cols[0].markdown("<div class='compact-header-left'>Account Hierarchy</div>", unsafe_allow_html=True)
    for i, p in enumerate(selected_periods):
        short_p = p[:3] + " " + p[-2:] if len(p) > 5 else p
        header_cols[i+1].markdown(f"<div class='compact-header'>{short_p}</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div class='compact-header'>TOTAL</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 2px 0 8px 0; border-color:#E2E8F0;'>", unsafe_allow_html=True)
    
    for cls_name, cls_data in hierarchy.items():
        cls_key = f"cls_{cls_name}"
        cls_open = cls_key in st.session_state.open_classifications
        cls_total = sum(cls_data['totals'].values())
        
        row_cols = st.columns(col_widths)
        arrow = "▼" if cls_open else "▶"
        
        with row_cols[0]:
            btn_label = f"{arrow} 📂 {cls_name}"
            if st.button(btn_label, key=f"btn_{cls_key}", use_container_width=True):
                if cls_open:
                    st.session_state.open_classifications.discard(cls_key)
                    st.session_state.open_accounts = {a for a in st.session_state.open_accounts if not a.startswith(f"acc_{cls_name}__")}
                else: st.session_state.open_classifications.add(cls_key)
                st.rerun()
        
        for i, p in enumerate(selected_periods):
            v = cls_data['totals'].get(p, 0)
            color = "#059669" if v > 0 else "#E11D48" if v < 0 else "#94A3B8"
            row_cols[i+1].markdown(f"<div style='text-align:right; font-weight:600; color:{color}; padding-top:4px; font-family:monospace; font-size:11px;'>{fmt_currency(v)}</div>", unsafe_allow_html=True)
        
        tc = "#059669" if cls_total > 0 else "#E11D48" if cls_total < 0 else "#94A3B8"
        row_cols[-1].markdown(f"<div style='text-align:right; font-weight:700; color:{tc}; padding-top:4px; font-family:monospace; font-size:11px; background:#EEF2F9; border-radius:4px; padding:4px 2px;'>{fmt_currency(cls_total)}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:2px; background:#EEF2F9; border-radius:1px; margin-bottom:2px;'></div>", unsafe_allow_html=True)
        
        if cls_open:
            for acc_name, acc_data in cls_data['accounts'].items():
                acc_key = f"acc_{cls_name}__{acc_name}"
                acc_open = acc_key in st.session_state.open_accounts
                acc_total = sum(acc_data['totals'].values())
                
                acc_cols = st.columns(col_widths)
                acc_arrow = "▼" if acc_open else "▶"
                
                with acc_cols[0]:
                    acc_btn_label = f"　　{acc_arrow} 📄 {acc_name}"
                    if st.button(acc_btn_label, key=f"btn_{acc_key}", use_container_width=True):
                        if acc_open: st.session_state.open_accounts.discard(acc_key)
                        else: st.session_state.open_accounts.add(acc_key)
                        st.rerun()
                
                for i, p in enumerate(selected_periods):
                    v = acc_data['totals'].get(p, 0)
                    color = "#059669" if v > 0 else "#E11D48" if v < 0 else "#94A3B8"
                    acc_cols[i+1].markdown(f"<div style='text-align:right; color:{color}; font-weight:500; padding-top:4px; font-family:monospace; font-size:10px;'>{fmt_currency(v)}</div>", unsafe_allow_html=True)
                
                at_color = "#059669" if acc_total > 0 else "#E11D48" if acc_total < 0 else "#94A3B8"
                acc_cols[-1].markdown(f"<div style='text-align:right; font-weight:600; color:{at_color}; padding-top:4px; font-family:monospace; font-size:10px;'>{fmt_currency(acc_total)}</div>", unsafe_allow_html=True)
                st.markdown("<div style='height:1px; background:#F1F5F9; margin-bottom:1px;'></div>", unsafe_allow_html=True)
                
                if acc_open:
                    for partner_name, prt_totals in acc_data['partners'].items():
                        prt_total = sum(prt_totals.values())
                        prt_cols = st.columns(col_widths)
                        
                        prt_cols[0].markdown(f"<div style='padding-left:100px; color:#64748B; font-size:9px; padding-top:3px;'>· {partner_name[:25]}{'...' if len(partner_name) > 25 else ''}</div>", unsafe_allow_html=True)
                        for i, p in enumerate(selected_periods):
                            v = prt_totals.get(p, 0)
                            color = "#059669" if v > 0 else "#E11D48" if v < 0 else "#94A3B8"
                            prt_cols[i+1].markdown(f"<div style='text-align:right; color:{color}; font-size:9px; padding-top:3px; font-family:monospace;'>{fmt_currency(v)}</div>", unsafe_allow_html=True)
                        
                        pt_color = "#059669" if prt_total > 0 else "#E11D48" if prt_total < 0 else "#94A3B8"
                        prt_cols[-1].markdown(f"<div style='text-align:right; color:{pt_color}; font-size:9px; padding-top:3px; font-family:monospace;'>{fmt_currency(prt_total)}</div>", unsafe_allow_html=True)
                        st.markdown("<div style='height:1px; background:#F8FAFC; margin-bottom:1px;'></div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color:#CBD5E1; margin: 6px 0;'>", unsafe_allow_html=True)
    gt_cols = st.columns(col_widths)
    gt_cols[0].markdown("<div style='font-weight:700; color:#0F2044; font-size:12px; padding-top:2px;'>📊 Grand Total</div>", unsafe_allow_html=True)
    for i, p in enumerate(selected_periods):
        gt_v = sum(cls_data['totals'].get(p, 0) for cls_data in hierarchy.values())
        color = "#059669" if gt_v > 0 else "#E11D48" if gt_v < 0 else "#94A3B8"
        gt_cols[i+1].markdown(f"<div style='text-align:right; font-weight:700; color:{color}; font-family:monospace; padding-top:2px; font-size:12px;'>{fmt_currency(gt_v)}</div>", unsafe_allow_html=True)
    
    grand_total = sum(sum(cls_data['totals'].values()) for cls_data in hierarchy.values())
    gt_color = "#059669" if grand_total > 0 else "#E11D48" if grand_total < 0 else "#94A3B8"
    gt_cols[-1].markdown(f"<div style='text-align:right; font-weight:700; color:{gt_color}; font-family:monospace; background:#EEF2F9; border-radius:4px; padding:4px 2px; font-size:12px;'>{fmt_currency(grand_total)}</div>", unsafe_allow_html=True)

# ===========================
# LEDGER EDITOR VIEW
# ===========================
elif view_mode == "✏️ Ledger Editor":
    st.write("Double-click the **Balance** cell to adjust values. Click **Save to Fabric** to commit.")

    if st.session_state.dirty: st.info("⚠️ You have pending edits. Click 'Save to Fabric' to commit.")

    base_display_cols = ['id', 'Store', 'classification', 'account_name', 'partner_id_name', 'Balance']
    editor_display_df = e_filtered[base_display_cols].copy()

    if editor_display_df.empty:
        st.warning("No records found for the selected filters.")
    else:
        st.markdown(f"<span style='color:#64748B; font-size:0.8rem; font-weight:500;'>{len(editor_display_df)} records ready for editing</span>", unsafe_allow_html=True)

        editor_df = st.data_editor(
            editor_display_df, key="editor", use_container_width=True, num_rows="fixed",
            disabled=[c for c in base_display_cols if c != 'Balance'],
            column_config={
                "id": None,
                "Balance": st.column_config.NumberColumn("Balance (₹)", help="Double click to edit", format="₹%.2f", step=0.01, required=True),
                "Store": st.column_config.TextColumn("Store", disabled=True),
                "classification": st.column_config.TextColumn("Classification", disabled=True),
                "account_name": st.column_config.TextColumn("Account", disabled=True),
                "partner_id_name": st.column_config.TextColumn("Partner", disabled=True)
            }
        )

        changed_mask = editor_df['Balance'] != editor_display_df['Balance']
        if changed_mask.any():
            st.session_state.dirty = True
            for idx in editor_df[changed_mask].index:
                row_id = editor_df.loc[idx, 'id']
                st.session_state.current_df.loc[st.session_state.current_df['id'] == row_id, 'Balance'] = editor_df.loc[idx, 'Balance']

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
                    success_count, error_count = 0, 0
                    progress_bar = st.progress(0)

                    for idx, (_, row) in enumerate(delta_rows.iterrows()):
                        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        variables = {
                            "id": int(row["id"]),
                            "balance": float(row["Balance"]) if pd.notnull(row["Balance"]) else 0.0,
                            "last_modified_at": current_time,
                            "last_modified_user": st.session_state.logged_in_user
                        }
                        try:
                            response = run_graphql(UPDATE_MUTATION, variables)
                            if "errors" not in response:
                                success_count += 1
                                st.session_state.current_df.loc[
                                    st.session_state.current_df['id'] == row['id'], ['last_modified_at', 'last_modified_user']
                                ] = [current_time, st.session_state.logged_in_user]
                            else: error_count += 1
                        except Exception: error_count += 1
                        progress_bar.progress((idx + 1) / len(delta_rows))

                    if error_count == 0:
                        st.session_state.original_df = st.session_state.current_df.copy()
                        st.session_state.dirty = False
                        load_data.clear()
                        st.success(f"✅ {success_count} changes saved successfully!")
                        st.balloons()
                        st.rerun()
                    elif success_count > 0:
                        st.warning(f"⚠️ {success_count} succeeded, {error_count} failed.")
                        st.session_state.original_df = st.session_state.current_df.copy()
                        st.session_state.dirty = False
                        load_data.clear()
                    else: st.error("❌ All updates failed. Please try again.")
