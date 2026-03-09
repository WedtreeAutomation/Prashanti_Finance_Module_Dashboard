​import streamlit as st
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
UPSERT_MUTATION = """
mutation upsertBalance($year: Int!, $monthName: String!, $store: String!, $balance: Float, $account_name: String!, $classification: String!, $partner_id_name: String!, $last_modified_at: DateTime, $last_modified_user: String) {
  executesp_upsertAccountBalance(year: $year, monthName: $monthName, store: $store, balance: $balance, account_name: $account_name, classification: $classification, partner_id_name: $partner_id_name, last_modified_at: $last_modified_at, last_modified_user: $last_modified_user) { rows_affected }
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
    
    # Define the desired order with more flexible matching
    # This list should match EXACTLY how they appear in your database
    classification_order = [
        'Income',
        'Other Income',
        'Employee cost',
        'Rent & Utilities',           # Exact match from your data
        'Marketing & Advertisment',    # Note: 'Advertisment' (missing 'e') as in your data
        'Admin Exp',        'Finance cost',
        'Other Expenses',
        'Supplier Payments',           # Exact match from your data
        'Purchase Expense',
        'Logistics',
        'Expense' 
    ]
    
    # Get unique classifications from the data
    unique_classifications = report_df['classification'].dropna().unique()
    
    # Create a custom sort key function
    def get_classification_order(cls):
        try:
            return classification_order.index(cls)
        except ValueError:
            # If classification not in our predefined list, print it for debugging
            print(f"Classification not in order list: '{cls}'")
            # Put it at the end, sorted alphabetically
            return len(classification_order) + (sum(ord(c) for c in cls) if cls else 0)
    
    # Sort classifications according to the defined order
    sorted_classifications = sorted(unique_classifications, key=get_classification_order)
    
    for classification in sorted_classifications:
        cls_df = report_df[report_df['classification'] == classification]
        cls_totals = {}
        for p in periods:
            cls_totals[p] = cls_df[cls_df['DisplayPeriod'] == p]['Balance'].sum()
        
        accounts = {}
        # Sort accounts alphabetically within each classification
        for account in sorted(cls_df['account_name'].dropna().unique()):
            acc_df = cls_df[cls_df['account_name'] == account]
            acc_totals = {}
            for p in periods:
                acc_totals[p] = acc_df[acc_df['DisplayPeriod'] == p]['Balance'].sum()
            
            partners = {}
            # Sort partners alphabetically within each account
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
    
    # Define the desired order matching your database exactly
    classification_order = [
        'Income',
        'Other Income',
        'Employee cost',
        'Rent & Utilities',           # Exact match from your data
        'Marketing & Advertisment',    # Note: 'Advertisment' (missing 'e') as in your data
        'Admin Exp',        'Finance cost',
        'Other Expenses',
        'Supplier Payments',           # Exact match from your data
        'Purchase Expense',
        'Logistics',
        'Expense'
    ]
    
    def get_classification_order(cls):
        try:
            return classification_order.index(cls)
        except ValueError:
            # If classification not in our predefined list, put it at the end
            return len(classification_order) + (sum(ord(c) for c in cls) if cls else 0)
    
    # Sort classifications according to the defined order
    sorted_classifications = sorted(hierarchy.keys(), key=get_classification_order)
    
    for cls_name in sorted_classifications:
        cls_data = hierarchy[cls_name]
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
        
        # Sort accounts alphabetically within each classification
        for acc_name in sorted(cls_data['accounts'].keys()):
            acc_data = cls_data['accounts'][acc_name]
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
            
            # Sort partners alphabetically within each account
            for partner_name in sorted(acc_data['partners'].keys()):
                prt_totals = acc_data['partners'][partner_name]
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
            username = st.text_input("Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", width = 'stretch', type="primary")
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
        st.markdown("<p style='color:#0F2044 !important; font-weight:600; font-size:1rem;'>📊 Report Filters</p>", unsafe_allow_html=True)
        
        # Add date range selection for editor
        editor_date_range_type = st.radio("Range Type", ["📅 Single/Multiple Months", "📆 Financial Year"], 
                                         horizontal=True, key="editor_range_type")
    
        if editor_date_range_type == "📅 Single/Multiple Months":
            editor_base_period = st.selectbox("Base Period", period_list, key="editor_base_period")
            editor_num_comparisons = st.number_input("Number of Periods", min_value=1, max_value=12, value=3, 
                                                    key="editor_num_comparisons", 
                                                    help="Total periods to display including base period")
            base_idx = period_list.index(editor_base_period)
            editor_selected_periods = period_list[base_idx: min(base_idx + editor_num_comparisons, len(period_list))]
        else:
            editor_available_years = sorted(df['Year'].dropna().unique(), reverse=True)
            editor_selected_year = st.selectbox("Financial Year (Apr–Mar)", editor_available_years, key="editor_year")
            fy_periods = get_financial_year_range(df, editor_selected_year, start_month=4)
            if fy_periods:
                editor_selected_periods = [p['display'] for p in fy_periods]
                st.info(f"{len(editor_selected_periods)} periods: {fy_periods[0]['display']} → {fy_periods[-1]['display']}")
            else:
                editor_selected_periods = []
    
        # Store filter for editor
        editor_store_filter = st.selectbox("🏢 Store", ["All"] + sorted(df['Store'].dropna().astype(str).unique()), 
                                          key="editor_store")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<p style='color:#0F2044 !important; font-weight:600; font-size:1rem;'>✏️ Editor Filters</p>", unsafe_allow_html=True)
        
        # Get filtered data based on selected periods and store
        if editor_selected_periods:
            editor_filtered_df = df[df['DisplayPeriod'].isin(editor_selected_periods)].copy()
            if editor_store_filter != "All":
                editor_filtered_df = editor_filtered_df[editor_filtered_df['Store'] == editor_store_filter]
            
            # Classification filter
            if not editor_filtered_df.empty:
                editor_class = st.selectbox("Class", ["All"] + sorted(editor_filtered_df['classification'].dropna().astype(str).unique()), 
                                           key="editor_class")
                if editor_class != "All":
                    editor_filtered_df = editor_filtered_df[editor_filtered_df['classification'] == editor_class]
                
                # Account filter
                if not editor_filtered_df.empty:
                    editor_account = st.selectbox("Account", ["All"] + sorted(editor_filtered_df['account_name'].dropna().astype(str).unique()), 
                                                 key="editor_account")
                    if editor_account != "All":
                        editor_filtered_df = editor_filtered_df[editor_filtered_df['account_name'] == editor_account]
                    
                    # Partner filter
                    if not editor_filtered_df.empty:
                        editor_partner = st.selectbox("Partner", ["All"] + sorted(editor_filtered_df['partner_id_name'].dropna().astype(str).unique()), 
                                                     key="editor_partner")
                        if editor_partner != "All":
                            editor_filtered_df = editor_filtered_df[editor_filtered_df['partner_id_name'] == editor_partner]
            
            # Store the filtered dataframe and selected periods in session state
            st.session_state.editor_filtered_df = editor_filtered_df
            st.session_state.editor_selected_periods = editor_selected_periods
            st.session_state.editor_store_filter = editor_store_filter
        else:
            st.session_state.editor_filtered_df = pd.DataFrame()
            st.session_state.editor_selected_periods = []
            st.warning("No periods selected.")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", width = 'stretch', type="secondary"):
        st.session_state.logged_in = False
        st.session_state.logged_in_user = ""
        st.query_params.clear() # Clears URL auth state token
        st.cache_data.clear()
        st.rerun()

# =============================
# MAIN CONTENT
# =============================
st.markdown(f'<div class="main-header">💠 {view_mode.split(" ", 1)[1]}</div>', unsafe_allow_html=True)

# =============================
# FINANCIAL INSIGHTS VIEW
# =============================
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
    st.plotly_chart(fig, width = 'stretch')

    st.markdown("---")
    
    hierarchy = build_hierarchy_data(report_df, selected_periods)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("### 📋 P&L Statement")
    with col2:
        export_col1, export_col2, export_col3 = st.columns([1, 1, 1])
        with export_col1:
            if st.button("⊞ Expand All", width = 'stretch'):
                for cls_name in hierarchy.keys():
                    st.session_state.open_classifications.add(f"cls_{cls_name}")
                    for acc_name in hierarchy[cls_name]['accounts'].keys():
                        st.session_state.open_accounts.add(f"acc_{cls_name}__{acc_name}")
                st.rerun()
        with export_col2:
            if st.button("Collapse All", width = 'stretch'):
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
                width = 'stretch', type="primary"
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
            if st.button(btn_label, key=f"btn_{cls_key}", width = 'stretch'):
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
                    if st.button(acc_btn_label, key=f"btn_{acc_key}", width = 'stretch'):
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
    # Check if we have filtered data from sidebar
    if not hasattr(st.session_state, 'editor_filtered_df') or st.session_state.editor_filtered_df.empty:
        st.info("ℹ️ Please select periods and filters in the sidebar to view/edit data.")
        st.stop()
    
    editor_df = st.session_state.editor_filtered_df
    editor_periods = st.session_state.editor_selected_periods
    editor_store = st.session_state.editor_store_filter
    
    # Display summary of current filter selection
    filter_summary = f"**Current View:** {len(editor_periods)} period(s): {', '.join(editor_periods)}"
    if editor_store != "All":
        filter_summary += f" | Store: {editor_store}"
    st.markdown(filter_summary)
    
    st.markdown("Double-click any period balance to edit. Changes will be reflected in the aggregated total.")

    # Define dimension columns WITHOUT id for grouping
    dimension_columns = ['Store', 'classification', 'account_name', 'partner_id_name']
    
    # First, verify we have data
    if editor_df.empty:
        st.warning("No records found for the selected filters.")
    else:
        # Create a pivot table with periods as columns, aggregating by the dimension columns
        # Group by the dimension columns and sum balances across any IDs that might exist
        pivot_df = editor_df.groupby(dimension_columns + ['DisplayPeriod'], as_index=False)['Balance'].sum()
        
        # Now pivot to get periods as columns
        pivot_df = pivot_df.pivot_table(
            index=dimension_columns,
            columns='DisplayPeriod',
            values='Balance',
            aggfunc='sum',
            fill_value=0.0
        ).reset_index()
        
        # Remove the columns index name
        pivot_df.columns.name = None
        
        # Get period columns (all columns not in dimension_columns)
        period_columns = [col for col in pivot_df.columns if col not in dimension_columns]
        
        # Sort period columns chronologically
        def get_period_sort_key(period):
            try:
                month_name, year = period.rsplit(' ', 1)
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                month_num = month_map.get(month_name, 0)
                return (int(year), month_num)
            except:
                return (9999, 99)
        
        if period_columns:
            period_columns = sorted(period_columns, key=get_period_sort_key)
            
            # Calculate total column
            pivot_df['Total'] = pivot_df[period_columns].sum(axis=1)
            
            # Reorder columns: dimension columns, then period columns, then total
            column_order = dimension_columns + period_columns + ['Total']
            pivot_df = pivot_df[column_order]
            
            # Ensure all numeric columns are properly typed
            for col in period_columns + ['Total']:
                pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0.0)
            
            # Sort for better organization
            pivot_df = pivot_df.sort_values(['classification', 'account_name', 'partner_id_name'])
            
            st.markdown(f"""
            <span style='color:#64748B; font-size:0.8rem; font-weight:500;'>
            {len(pivot_df)} unique account-partner combinations | 
            Showing balances for {len(period_columns)} periods: {period_columns[0]} → {period_columns[-1]}
            </span>
            """, unsafe_allow_html=True)

            # Create column configuration for the editor
            column_config = {
                "Store": st.column_config.TextColumn("Store", disabled=True, width="small"),
                "classification": st.column_config.TextColumn("Classification", disabled=True),
                "account_name": st.column_config.TextColumn("Account", disabled=True),
                "partner_id_name": st.column_config.TextColumn("Partner", disabled=True),
                "Total": st.column_config.NumberColumn(
                    "Total (All Periods)",
                    help="Aggregated total across all selected periods",
                    format="₹%.2f",
                    disabled=True,  # Total is calculated, not editable directly
                )
            }
            
            # Add dynamic column configs for each period
            for period in period_columns:
                # Create a short period name for display
                try:
                    month_name, year = period.rsplit(' ', 1)
                    short_period = month_name[:3] + " " + year[-2:]
                except:
                    short_period = period
                
                column_config[period] = st.column_config.NumberColumn(
                    short_period,
                    help=f"Double click to edit balance for {period}",
                    format="₹%.2f",
                    step=0.01,
                    required=True
                )

            # Apply filters to the pivot table
            filtered_pivot_df = pivot_df.copy()

            if 'editor_class' in st.session_state and st.session_state.editor_class != "All":
                filtered_pivot_df = filtered_pivot_df[filtered_pivot_df['classification'] == st.session_state.editor_class]
            if 'editor_account' in st.session_state and st.session_state.editor_account != "All":
                filtered_pivot_df = filtered_pivot_df[filtered_pivot_df['account_name'] == st.session_state.editor_account]
            if 'editor_partner' in st.session_state and st.session_state.editor_partner != "All":
                filtered_pivot_df = filtered_pivot_df[filtered_pivot_df['partner_id_name'] == st.session_state.editor_partner]

            # Display the editor
            # Note: key="editor" is vital for Streamlit to track state
            editor_df_widget = st.data_editor(
                filtered_pivot_df, 
                key="editor", 
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=['Store', 'classification', 'account_name', 'partner_id_name', 'Total'],
                column_config=column_config
            )

            # 2. Identify Changes
            changes_summary = []
            for idx in editor_df_widget.index:
                for period in period_columns:
                    original_val = float(filtered_pivot_df.loc[idx, period])
                    new_val = float(editor_df_widget.loc[idx, period])
                    
                    if abs(original_val - new_val) > 0.001:
                        changes_summary.append({
                            'store': editor_df_widget.loc[idx, 'Store'],
                            'classification': editor_df_widget.loc[idx, 'classification'],
                            'account': editor_df_widget.loc[idx, 'account_name'],
                            'partner': editor_df_widget.loc[idx, 'partner_id_name'],
                            'period': period,
                            'new_value': new_val
                        })

            # 3. Update Dirty State
            st.session_state.dirty = len(changes_summary) > 0

            if st.session_state.dirty:
                st.info(f"📝 {len(changes_summary)} pending changes.")

            st.write("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([6, 2, 2])

            with col2:
                if st.button("🗑️ Discard", use_container_width=True, disabled=not st.session_state.dirty):
                    if "editor" in st.session_state:
                        del st.session_state["editor"]
                    st.session_state.dirty = False
                    st.rerun()

            # 4. Save Logic
            with col3:
                if st.button("💾 Save to Fabric", use_container_width=True, disabled=not st.session_state.dirty, type="primary"):
                    with st.spinner("Syncing changes with Fabric..."):
                        success_count, error_count = 0, 0
                        
                        month_map = {
                            "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
                            "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
                            "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"
                        }

                        # Consistent timestamp for all records in this batch
                        current_time_fabric = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                        for change in changes_summary:
                            # 1. CLEAN YEAR PARSING
                            p_parts = change['period'].split()
                            full_month = month_map.get(p_parts[0], p_parts[0])
                            
                            raw_year = p_parts[1]
                            # Handle both "26" and "2026" formats
                            if len(raw_year) == 2:
                                full_year = 2000 + int(raw_year)
                            else:
                                full_year = int(raw_year)
                            
                            # 2. ALIGN DIMENSIONS
                            # Ensure dimension values are stripped of whitespace to match SQL JOIN logic
                            variables = {
                                "year": full_year,
                                "monthName": full_month,
                                "store": str(change['store']).strip(),
                                "balance": float(change['new_value']),
                                "account_name": str(change['account']).strip(),
                                "classification": str(change['classification']).strip(),
                                "partner_id_name": str(change['partner']).strip(),
                                "last_modified_at": current_time_fabric,
                                "last_modified_user": st.session_state.logged_in_user
                            }

                            try:
                                # The Fabric Stored Procedure logic (provided in previous step)
                                # will now use these variables to either UPDATE an existing match
                                # or INSERT if no Store/Account/Year/Month match exists.
                                response = run_graphql(UPSERT_MUTATION, variables)
                                
                                if response and "errors" not in response:
                                    success_count += 1
                                else:
                                    error_msg = response['errors'][0]['message'] if response else "No response"
                                    st.error(f"Failed to save {change['account']}: {error_msg}")
                                    error_count += 1
                            except Exception as e:
                                st.error(f"Connection error: {str(e)}")
                                error_count += 1

                        # 3. UI STATE REFRESH
                        if error_count == 0:
                            st.success(f"✅ Successfully synced {success_count} records to Fabric!")
                            # Clear cache so the 'readData' query fetches the newly updated values
                            load_data.clear() 
                            
                            # Clear transient session states
                            if "editor" in st.session_state:
                                del st.session_state["editor"]
                            st.session_state.dirty = False
                            
                            # Rerun to show the updated table immediately
                            st.rerun()
                        else:
                            st.warning(f"Process complete: {success_count} saved, {error_count} failed.")
