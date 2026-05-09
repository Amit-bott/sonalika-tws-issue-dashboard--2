import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from streamlit_lottie import st_lottie
from datetime import datetime
import time
import sqlite3
import os

# ─────────────────────────────────────────────────────────────────────────────
#  DATABASE  (identical to original Connect.py)
# ─────────────────────────────────────────────────────────────────────────────
def make_connection():
    conn = sqlite3.connect('Layout.db', check_same_thread=False)
    return conn

conn   = make_connection()
cursor = conn.cursor()

def create_table():
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Layout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Email TEXT NOT NULL UNIQUE,
                Password TEXT NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")

create_table()

class Connect:
    @staticmethod
    def login(username, password):
        sql = "SELECT Name, Email FROM Layout WHERE Name=? AND Password=?"
        try:
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            return (user[0], user[0]) if user else None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    @staticmethod
    def registration(username, email, password):
        sql = "INSERT INTO Layout (Name, Email, Password) VALUES (?, ?, ?)"
        try:
            cursor.execute(sql, (username, email, password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Registration failed: {e}")
            return False

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

lottie_loading = load_lottieurl(
    "https://lottie.host/db1d952d-60a0-4bd6-bbb1-11fa885687bc/tlQrUeuvPY.json"
)

# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR MAPS
# ─────────────────────────────────────────────────────────────────────────────
CONTINENT_COLORS = {
    'Asia':    ['#00E5FF', '#0891B2', '#38BDF8', '#7DD3FC'],
    'Europe':  ['#FFD700', '#F59E0B', '#FCD34D', '#FDE68A'],
    'America': ['#00FF9D', '#16A34A', '#4ADE80', '#86EFAC'],
    'Africa':  ['#FF6B35', '#EA580C', '#FB923C', '#FDBA74'],
    'Oceania': ['#FF4DFF', '#DB2777', '#F472B6', '#FBCFE8'],
    'Unknown': ['#94A3B8', '#64748B', '#CBD5E1', '#E2E8F0'],
}

def get_cont_colors(continent: str):
    return CONTINENT_COLORS.get(str(continent).strip(), CONTINENT_COLORS['Unknown'])

MILE_COL = {
    'Implemented':                                      '#16A34A',
    'Field Information Awaited':                        '#2563EB',
    'Field information awaited':                        '#2563EB',
    'RCA in CFT - Under Study':                         '#D97706',
    'Design Review - Feasibility Study':                '#7C3AED',
    'Supplier Action - Actions awaited':                '#EA580C',
    'Under Implementation':                             '#0891B2',
    'RCA in CFT - Failed Part Analysis':                '#DC2626',
    'Failed part awaited':                              '#DB2777',
    'Material Availability':                            '#65A30D',
    'TWS/ IPE Project':                                 '#1E3A8A',
    'TWS/ IPE Project - Testing/ Validation/ Fitment':  '#3B82F6',
    'Closed':                                           '#6B7280',
}

MILE_SHORT = {
    'Field Information Awaited':                        'Field Info Awaited',
    'RCA in CFT - Under Study':                         'RCA - Under Study',
    'Design Review - Feasibility Study':                'Design Review',
    'Supplier Action - Actions awaited':                'Supplier Action',
    'RCA in CFT - Failed Part Analysis':                'RCA - Failed Part',
    'TWS/ IPE Project - Testing/ Validation/ Fitment':  'TWS/IPE Testing',
}

DEPT_COL = {
    'CFT':                 '#2563EB',
    'Closed':              '#16A34A',
    'Service':             '#D97706',
    'R&D':                 '#7C3AED',
    'IQC':                 '#EA580C',
    'Purchase':            '#DB2777',
    'Business Excellence': '#0891B2',
    'Engine Assembly':     '#DC2626',
}

# ISO-3 country codes for choropleth world map
COUNTRY_ISO3 = {
    'Thailand':      'THA', 'Nepal':          'NPL', 'Brazil':       'BRA',
    'Bangladesh':    'BGD', 'USA':            'USA', 'Portugal':     'PRT',
    'Myanmar':       'MMR', 'Poland':         'POL', 'Denmark':      'DNK',
    'Mexico':        'MEX', 'UK':             'GBR', 'Turkey':       'TUR',
    'FIJI':          'FJI', 'Afghanistan':    'AFG', 'Arjentina':    'ARG',
    'Czech Republic':'CZE', 'Finland':        'FIN', 'Finlanad':     'FIN',
    'Moldova':       'MDA', 'Belaruse':       'BLR', 'Romania':      'ROU',
    'Algeria':       'DZA', 'Morraco':        'MAR', 'Tunisia':      'TUN',
    'Tanzania':      'TZA', 'Nepal Solis':    'NPL', 'Vietnam':      'VNM',
    'Keneya':        'KEN', 'South Africa':   'ZAF', 'Australia':    'AUS',
    'ITLAY':         'ITA', 'Netherlands':    'NLD',
}

# ─────────────────────────────────────────────────────────────────────────────
#  AUTH DISPLAY FUNCTIONS  (identical to original)
# ─────────────────────────────────────────────────────────────────────────────
def display_protected_project_page():
    st.sidebar.header("User Dashboard")
    st.sidebar.success(f"Access granted to: {st.session_state.username}")
    if st.sidebar.button("Logout", help="Click to log out of the application"):
        st.session_state.logged_in = False
        st.session_state.username  = None
        st.info("Logged out successfully.")
        st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Project Filters & Controls**")
    project_dashboard()


def display_login_or_register():
    LOTTIE_URL_LOCK     = "https://lottie.host/3ccff03a-36c7-4b15-81bf-54ee3362e18f/NfxIBmRe5o.json"
    LOTTIE_URL_REGISTER = "https://lottie.host/0715fade-5bd0-44af-881f-f61d67d55c73/J5rgz04sDq.json"
    lottie_lock     = load_lottieurl(LOTTIE_URL_LOCK)
    lottie_register = load_lottieurl(LOTTIE_URL_REGISTER)

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.header("Login")
        col1, col2 = st.columns([1, 2])
        with col1:
            if lottie_lock:
                st_lottie(lottie_lock, speed=1, loop=True, quality="high",
                          height=400, width=400, key="lock_animation")
            else:
                st.info("Lottie animation space (could not load remote content).")
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In"):
                    if username and password:
                        user_data = Connect.login(username, password)
                        if user_data:
                            st.session_state.logged_in = True
                            st.session_state.username  = user_data[0]
                            st.success("Logged in successfully! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                    else:
                        st.error("Please enter both username and password.")

    with register_tab:
        st.header("Register")
        col1, col2 = st.columns([1, 2])
        with col1:
            if lottie_register:
                st_lottie(lottie_register, speed=1, loop=True, quality="high",
                          height=400, width=400, key="register_animation")
            else:
                st.info("Lottie animation space (could not load remote content).")
        with col2:
            with st.form("register_form"):
                new_username = st.text_input("New Username")
                new_email    = st.text_input("Email")
                new_password = st.text_input("New Password", type="password")
                if st.form_submit_button("Register"):
                    if new_username and new_email and new_password:
                        if Connect.registration(new_username, new_email, new_password):
                            st.success("Registration successful! You can now log in.")
                        else:
                            st.error("Registration failed. Username or email may already exist.")
                    else:
                        st.error("Please fill in all fields.")


def main():
    st.set_page_config(
        page_title="Issues Intelligence Dashboard",
        page_icon="🔐",
        initial_sidebar_state='auto',
        layout='wide'
    )
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50; color: white; font-weight: bold;
            border-radius: 8px; border: none; padding: 10px 24px; cursor: pointer;
        }
        .stButton>button:hover { background-color: #45a049; }
        div.stApp { font-size: 1.15rem; }
        .stApp p   { font-size: 1.25rem !important; line-height: 1.6; }
        .stDataFrame { font-size: 1rem; }
        </style>
    """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username  = None

    if st.session_state.logged_in:
        display_protected_project_page()
    else:
        st.title("User Authentication App")
        st.caption("Please log in to access the Issues Intelligence Dashboard.")
        display_login_or_register()

# ─────────────────────────────────────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _expand_countries(data: pd.DataFrame) -> pd.DataFrame:
    """One row per country — handles 'UK, Finland' style entries."""
    rows = []
    for _, row in data.iterrows():
        if pd.isna(row.get('Country')):
            rows.append(row.to_dict())
            continue
        parts = (str(row['Country'])
                 .replace(' and ', ',').replace('&', ',').split(','))
        seen = set()
        for p in parts:
            c = p.strip()
            if c and c not in seen:
                seen.add(c)
                d = row.to_dict(); d['Country'] = c; rows.append(d)
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def project_dashboard():
    """Issues Intelligence Dashboard - same structure as original Walmart dashboard."""

    st.title("Issues Intelligence Dashboard 📊")
    st.markdown("""
    Welcome to the interactive **Issues Data Dashboard**.
    Upload your Excel file from the sidebar, apply filters and explore all metrics
    through **interactive Plotly charts** including a live **World Map**.
    """)

    # ── Sidebar: upload ───────────────────────────────────────────────────────
    st.sidebar.header("Upload Issues Excel File")
    uploaded_file = st.sidebar.file_uploader(
        "Choose an Excel (.xlsx) file", type=["xlsx", "xls"]
    )

    if uploaded_file is None:
        st.info("Please upload an Excel file from the sidebar to begin.")
        return

    # ── Load data ─────────────────────────────────────────────────────────────
    @st.cache_data
    def load_data(file):
        data = pd.read_excel(file)
        if 'HP category' in data.columns:
            data['HP category'] = data['HP category'].str.strip()
            data.loc[data['HP category'] == '30-60 HP', 'HP category'] = '30 - 60 HP'
        if 'Current Milestone' in data.columns:
            data['Current Milestone'] = data['Current Milestone'].fillna('').str.strip()
            data.loc[data['Current Milestone'] == 'Field information awaited',
                     'Current Milestone'] = 'Field Information Awaited'
        for col in ['Issue diss. Date', 'Closure Month', 'Cut off Date / Closure Date']:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col], errors='coerce')
        for col in ['Milestone Target Date', 'Closure Month - Plan']:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col], errors='coerce')
        if 'Aging' in data.columns:
            data['Aging'] = pd.to_numeric(data['Aging'], errors='coerce')
            data['Aging'] = data['Aging'].where(data['Aging'] < 500)
        data = _expand_countries(data)
        data['ISO3'] = data['Country'].map(COUNTRY_ISO3)
        return data

    ph = st.empty()
    with ph.container():
        st.info('Reading and processing data from Excel...')
        if lottie_loading:
            st_lottie(lottie_loading, height=200, key="loading_initial")
        try:
            df = load_data(uploaded_file)
        except Exception as e:
            st.error(f"Failed to load data. Error: {e}")
            return
    ph.empty()

    required = ['Ser. No', 'Country', 'Continent', 'Current Milestone',
                'Department', 'HP category', 'Issue diss. Date', 'Aging']
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing columns: **{', '.join(missing)}**")
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.header("Filter Data")
    continents   = sorted(df['Continent'].dropna().unique().tolist())
    sel_cont     = st.sidebar.selectbox("Select Continent", ["All"] + continents)
    pool_df      = df if sel_cont == "All" else df[df['Continent'] == sel_cont]
    sel_country  = st.sidebar.selectbox(
        "Select Country", ["All"] + sorted(pool_df['Country'].dropna().unique().tolist())
    )
    issue_types     = sorted(df['Issue Type'].dropna().unique().tolist()) if 'Issue Type' in df.columns else []
    sel_issue_types = st.sidebar.multiselect("Issue Type", issue_types, default=issue_types)
    departments = sorted(df['Department'].dropna().unique().tolist())
    sel_depts   = st.sidebar.multiselect("Department", departments, default=departments)
    hp_cats     = sorted(df['HP category'].dropna().unique().tolist())
    sel_hp      = st.sidebar.multiselect("HP Category", hp_cats, default=hp_cats)
    milestones  = sorted(df['Current Milestone'].replace('', pd.NA).dropna().unique().tolist())
    sel_miles   = st.sidebar.multiselect("Milestone Status", milestones, default=milestones)
    valid_dates = df['Issue diss. Date'].dropna()
    if len(valid_dates):
        min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
        date_range   = st.sidebar.date_input(
            "Issue Date Range", value=(min_d, max_d),
            min_value=min_d, max_value=max_d
        )
    else:
        date_range = None

    # ── Apply filters ─────────────────────────────────────────────────────────
    fdf = df.copy()
    if sel_cont    != "All":                             fdf = fdf[fdf['Continent'] == sel_cont]
    if sel_country != "All":                             fdf = fdf[fdf['Country']   == sel_country]
    if sel_issue_types and 'Issue Type' in fdf.columns:  fdf = fdf[fdf['Issue Type'].isin(sel_issue_types)]
    if sel_depts:                                        fdf = fdf[fdf['Department'].isin(sel_depts)]
    if sel_hp:                                           fdf = fdf[fdf['HP category'].isin(sel_hp)]
    if sel_miles:                                        fdf = fdf[fdf['Current Milestone'].isin(sel_miles)]
    if date_range and len(date_range) == 2:
        fdf = fdf[
            (fdf['Issue diss. Date'] >= pd.Timestamp(date_range[0])) &
            (fdf['Issue diss. Date'] <= pd.Timestamp(date_range[1]))
        ]

    if fdf.empty:
        st.warning("No data found for the selected filters. Please adjust your selections.")
        return

    col_set = get_cont_colors(sel_cont if sel_cont != "All" else "Unknown")

    with st.spinner('Generating visualisations...'):
        time.sleep(0.3)

    with st.expander(f"Raw Data - {len(fdf)} records (click to expand)"):
        st.dataframe(fdf, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.header("Plot Customisation")
    n_bins = st.sidebar.slider("Bins for Aging Distribution", 5, 60, 20)

    # ══════════════════════════════════════════════════════════════════════════
    #  KPI METRICS — Clickable cards with full detail table
    # ══════════════════════════════════════════════════════════════════════════
    st.header("Key Performance Indicators")
    st.caption("👇 Kisi bhi KPI button par click karo — us category ki poori issues list neeche dikhe gi")

    total_issues  = int(fdf['Ser. No'].nunique())
    pdi_count     = int((fdf['Issue Type'] == 'PDI').sum()) if 'Issue Type' in fdf.columns else 0
    svc_count     = int((fdf['Issue Type'] == 'Service').sum()) if 'Issue Type' in fdf.columns else 0
    avg_aging     = round(fdf['Aging'].dropna().mean(), 1) if fdf['Aging'].notna().any() else 0
    implemented   = int((fdf['Current Milestone'] == 'Implemented').sum())
    countries_aff = int(fdf['Country'].nunique())
    open_issues   = total_issues - implemented

    # Session state for KPI selection
    if 'kpi_selected' not in st.session_state:
        st.session_state.kpi_selected = None

    # KPI card HTML style
    st.markdown("""
    <style>
    div[data-testid="column"] .stButton button {
        width: 100%;
        height: 90px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: bold;
        border: 2px solid rgba(255,255,255,0.15);
        transition: all 0.2s ease;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        padding: 6px;
        line-height: 1.4;
    }
    div[data-testid="column"] .stButton button:hover {
        border-color: #00e5ff;
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,229,255,0.25);
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    kpi_defs = [
        (c1, "kpi_total",     "📋 Total Issues",       total_issues,  "#00E5FF"),
        (c2, "kpi_pdi",       "🔧 PDI Issues",          pdi_count,     "#FFD700"),
        (c3, "kpi_service",   "⚙️ Service Issues",      svc_count,     "#FF6B35"),
        (c4, "kpi_aging",     "⏳ Avg Aging (days)",    avg_aging,     "#F472B6"),
        (c5, "kpi_impl",      "✅ Implemented",          implemented,   "#4ADE80"),
        (c6, "kpi_open",      "🔴 Open Issues",          open_issues,   "#EF4444"),
        (c7, "kpi_countries", "🌍 Countries Affected",  countries_aff, "#A78BFA"),
    ]

    for col, key, label, value, color in kpi_defs:
        with col:
            selected = st.session_state.kpi_selected == key
            border   = color if selected else "rgba(255,255,255,0.15)"
            st.markdown(
                f"""<div style='background:linear-gradient(135deg,#1e293b,#0f172a);
                    border:2px solid {border};border-radius:12px;padding:12px 8px;
                    text-align:center;cursor:pointer;
                    box-shadow:{"0 0 16px " + color + "55" if selected else "none"};'>
                    <div style='font-size:11px;color:#94a3b8;font-weight:600;'>{label}</div>
                    <div style='font-size:28px;font-weight:900;color:{color};'>{value}</div>
                </div>""",
                unsafe_allow_html=True
            )
            btn_label = "▼ Hide" if selected else "▶ Details"
            if st.button(btn_label, key=f"btn_{key}"):
                st.session_state.kpi_selected = None if selected else key

    # ── KPI DETAIL PANEL ─────────────────────────────────────────────────────
    sel = st.session_state.kpi_selected
    if sel:
        st.markdown("---")

        DETAIL_COLS = ['Ser. No', 'Issue Type', 'Issue Description', 'Country',
                       'Continent', 'Model', 'HP category', 'Current Milestone',
                       'Department', 'Responsibility', 'Issue diss. Date',
                       'Milestone Target Date', 'Closure Month - Plan',
                       'Closure Month', 'Aging', 'No of Failure']
        show_cols = [c for c in DETAIL_COLS if c in fdf.columns]

        if sel == "kpi_total":
            st.subheader(f"📋 All Issues — {total_issues} records")
            detail_df = fdf[show_cols].sort_values('Ser. No')

        elif sel == "kpi_pdi":
            st.subheader(f"🔧 PDI Issues — {pdi_count} records")
            detail_df = fdf[fdf['Issue Type'] == 'PDI'][show_cols].sort_values('Ser. No')

        elif sel == "kpi_service":
            st.subheader(f"⚙️ Service Issues — {svc_count} records")
            detail_df = fdf[fdf['Issue Type'] == 'Service'][show_cols].sort_values('Ser. No')

        elif sel == "kpi_aging":
            st.subheader(f"⏳ Aging Detail — Avg {avg_aging} days")
            aging_df = fdf.dropna(subset=['Aging'])[show_cols + []].sort_values('Aging', ascending=False)
            st.markdown(f"**Highest Aging Issues (Top 20):**")
            detail_df = aging_df.head(20)
            # Summary stats
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Min Aging",    f"{int(fdf['Aging'].dropna().min())} days")
            sc2.metric("Max Aging",    f"{int(fdf['Aging'].dropna().max())} days")
            sc3.metric("Median",       f"{int(fdf['Aging'].dropna().median())} days")
            sc4.metric("Avg",          f"{avg_aging} days")

            # Aging bar chart
            aging_bar = (fdf.dropna(subset=['Aging'])
                            .sort_values('Aging', ascending=False)
                            .head(20))
            aging_bar['Label'] = aging_bar['Ser. No'].astype(str) + ' - ' + aging_bar['Issue Description'].str[:30]
            fig_age = px.bar(aging_bar, x='Aging', y='Label', orientation='h',
                             color='Aging', color_continuous_scale='RdYlGn_r',
                             labels={'Aging':'Days','Label':'Issue'},
                             template='plotly_dark', text='Aging')
            fig_age.update_layout(height=500, showlegend=False,
                                  coloraxis_showscale=False,
                                  yaxis=dict(tickfont=dict(size=9)))
            fig_age.update_traces(textposition='outside')
            st.plotly_chart(fig_age, use_container_width=True)

        elif sel == "kpi_impl":
            st.subheader(f"✅ Implemented Issues — {implemented} records")
            detail_df = fdf[fdf['Current Milestone'] == 'Implemented'][show_cols].sort_values('Ser. No')

        elif sel == "kpi_open":
            st.subheader(f"🔴 Open Issues — {open_issues} records")
            open_df = fdf[fdf['Current Milestone'] != 'Implemented']
            detail_df = open_df[show_cols].sort_values('Aging', ascending=False)
            # Milestone breakdown of open issues
            mile_open = (open_df.groupby('Current Milestone')['Ser. No']
                                .count().reset_index()
                                .rename(columns={'Ser. No':'Count'})
                                .sort_values('Count', ascending=True))
            fig_open = px.bar(mile_open, y='Current Milestone', x='Count',
                              orientation='h',
                              color='Current Milestone',
                              color_discrete_map={m: MILE_COL.get(m,'#94A3B8') for m in mile_open['Current Milestone']},
                              template='plotly_dark', text='Count',
                              labels={'Count':'Issues','Current Milestone':'Milestone'})
            fig_open.update_layout(showlegend=False, height=380,
                                   yaxis=dict(tickfont=dict(size=9)))
            fig_open.update_traces(textposition='outside')
            st.plotly_chart(fig_open, use_container_width=True)

        elif sel == "kpi_countries":
            st.subheader(f"🌍 Countries Affected — {countries_aff} countries")
            country_sum = (fdf.groupby(['Country','Continent'])['Ser. No']
                              .count().reset_index()
                              .rename(columns={'Ser. No':'Issue Count'})
                              .sort_values('Issue Count', ascending=False))
            cont_col_map = {c: CONTINENT_COLORS.get(c,['#94A3B8'])[0]
                            for c in country_sum['Continent'].unique()}
            fig_cmap = px.bar(country_sum, x='Issue Count', y='Country',
                              orientation='h', color='Continent',
                              color_discrete_map=cont_col_map,
                              template='plotly_dark', text='Issue Count',
                              labels={'Issue Count':'Issues','Country':'Country'})
            fig_cmap.update_layout(height=max(400, len(country_sum)*22),
                                   yaxis=dict(tickfont=dict(size=9),autorange='reversed'))
            fig_cmap.update_traces(textposition='outside')
            st.plotly_chart(fig_cmap, use_container_width=True)
            detail_df = country_sum

        # Show detail table for all KPIs (except aging which already has it)
        if sel != "kpi_aging" and 'detail_df' in dir():
            st.markdown(f"**Full Data Table ({len(detail_df)} rows):**")
            # Format date columns nicely
            display_df = detail_df.copy()
            for dcol in ['Issue diss. Date','Milestone Target Date',
                         'Closure Month - Plan','Closure Month']:
                if dcol in display_df.columns:
                    display_df[dcol] = pd.to_datetime(
                        display_df[dcol], errors='coerce'
                    ).dt.strftime('%d %b %Y').fillna('—')
            if 'Aging' in display_df.columns:
                display_df['Aging'] = display_df['Aging'].apply(
                    lambda x: f"{int(x)} days" if pd.notna(x) else '—'
                )
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Download button
            csv = detail_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Download this data as CSV",
                data=csv,
                file_name=f"{sel.replace('kpi_','')}_issues.csv",
                mime='text/csv'
            )
    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    #  VIOLIN + BOX  (same layout as original plots 7 & 8)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("Aging Distribution - Violin & Box Plot")
    vcol1, vcol2 = st.columns(2)

    with vcol1:
        st.markdown("##### Violin Plot - Aging (Days)")
        fig_v = px.violin(
            fdf.dropna(subset=['Aging']), y='Aging',
            box=True, points="all",
            labels={'Aging': 'Aging (Days)'},
            color_discrete_sequence=[col_set[0]],
            template='plotly_dark'
        )
        fig_v.update_layout(xaxis={'visible': False, 'showticklabels': False})
        st.plotly_chart(fig_v, use_container_width=True, height=600)

    with vcol2:
        st.markdown("##### Box Plot - Aging by Department")
        dept_aging = fdf.dropna(subset=['Aging', 'Department'])
        fig_b = px.box(
            dept_aging, x='Department', y='Aging',
            labels={'Aging': 'Aging (Days)', 'Department': 'Department'},
            color='Department',
            color_discrete_map={d: DEPT_COL.get(d, '#999') for d in dept_aging['Department'].unique()},
            template='plotly_dark'
        )
        fig_b.update_layout(showlegend=False, xaxis_tickangle=-30, height=600)
        st.plotly_chart(fig_b, use_container_width=True, height=600)

    # ══════════════════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3 = st.tabs([
        "Timeline & Distribution",
        "World Map & Geography",
        "Milestone & Correlations",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 1 - Timeline & Distribution
    # ─────────────────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Issue Count Over Time (Weekly)")
        time_df = (fdf.dropna(subset=['Issue diss. Date'])
                      .set_index('Issue diss. Date')
                      .resample('W')['Ser. No']
                      .count()
                      .reset_index()
                      .rename(columns={'Issue diss. Date': 'Week', 'Ser. No': 'Issues'}))
        fig_line = px.line(
            time_df, x='Week', y='Issues',
            labels={'Issues': 'Issues Raised per Week'},
            color_discrete_sequence=[col_set[2]],
            template='plotly_dark', markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True, height=450)

        st.subheader("Aging Distribution")
        st.markdown(f"Histogram of **Aging (days)** with **{n_bins}** bins.")
        fig_hist = go.Figure(data=[go.Histogram(
            x=fdf['Aging'].dropna(), nbinsx=n_bins,
            marker_color=col_set[1],
            marker_line_color='black', marker_line_width=1.5
        )])
        fig_hist.update_layout(
            xaxis_title_text='Aging (Days)',
            yaxis_title_text='Frequency',
            template='plotly_dark', height=420
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        st.subheader("Total Issues: PDI vs Service")
        if 'Issue Type' in fdf.columns:
            type_grp = (fdf.groupby('Issue Type')['Ser. No']
                           .count().reset_index()
                           .rename(columns={'Ser. No': 'Count'}))
            color_map_type = dict(zip(type_grp['Issue Type'].tolist(), [col_set[2], col_set[3]]))
            fig_bar = px.bar(
                type_grp, x='Issue Type', y='Count',
                labels={'Count': 'Number of Issues'},
                color='Issue Type', color_discrete_map=color_map_type,
                template='plotly_dark', text='Count'
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True, height=420)

        # ── GANTT TIMELINE ─────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Gantt Timeline  -  Issue Date to Milestone Target to Plan Close to Actual Close")
        st.caption("Bar = open period  |  Diamond = Milestone Target  |  Triangle = Plan Close  |  Star = Actual Close  |  Red line = Today")

        TODAY     = pd.Timestamp('2026-02-17')
        TODAY_STR = TODAY.strftime('%Y-%m-%d')

        tl_df = fdf.dropna(subset=['Issue diss. Date']).sort_values('Issue diss. Date').copy()
        tl_df['_target'] = pd.to_datetime(tl_df['Milestone Target Date'], errors='coerce')
        tl_df['_plan']   = pd.to_datetime(tl_df['Closure Month - Plan'],  errors='coerce')
        tl_df['_actual'] = pd.to_datetime(tl_df['Closure Month'],          errors='coerce')

        if len(tl_df):
            fig_gantt = go.Figure()

            for _, row in tl_df.iterrows():
                iss    = row['Issue diss. Date']
                tgt    = row['_target']  if pd.notna(row['_target'])  else None
                plan   = row['_plan']    if pd.notna(row['_plan'])    else None
                actual = row['_actual']  if pd.notna(row['_actual'])  else None
                mile   = str(row.get('Current Milestone', '')) or 'Unknown'
                mcolor = MILE_COL.get(mile, '#94A3B8')
                end_dt = actual or plan or tgt or TODAY
                if end_dt < iss:
                    end_dt = TODAY
                label     = f"#{int(row['Ser. No'])}  {str(row.get('Issue Description',''))[:38]}"
                aging_val = int(row['Aging']) if pd.notna(row.get('Aging')) else '-'
                hover = (
                    f"<b>#{int(row['Ser. No'])}</b>  {row.get('Issue Description','')}<br>"
                    f"<b>Country:</b> {row.get('Country','')}<br>"
                    f"<b>Continent:</b> {row.get('Continent','')}<br>"
                    f"<b>Milestone:</b> {mile}<br>"
                    f"<b>Issue Date:</b> {iss.strftime('%d %b %Y')}<br>"
                    f"<b>Target:</b> {tgt.strftime('%d %b %Y') if tgt else '-'}<br>"
                    f"<b>Plan Close:</b> {plan.strftime('%d %b %Y') if plan else '-'}<br>"
                    f"<b>Actual Close:</b> {actual.strftime('%d %b %Y') if actual else '-'}<br>"
                    f"<b>Aging:</b> {aging_val} days<br>"
                    f"<b>Dept:</b> {row.get('Department','')}"
                )

                # Base bar
                fig_gantt.add_trace(go.Bar(
                    x=[(end_dt - iss).days],
                    base=[iss.strftime('%Y-%m-%d')],
                    y=[label], orientation='h',
                    marker_color=mcolor, opacity=0.45,
                    hovertext=hover, hoverinfo='text',
                    showlegend=False, width=0.55, name=''
                ))
                if tgt:
                    fig_gantt.add_trace(go.Scatter(
                        x=[tgt.strftime('%Y-%m-%d')], y=[label], mode='markers',
                        marker=dict(symbol='diamond', size=11,
                                    color='#FBBF24', line=dict(color='white', width=1)),
                        hovertext=f"<b>Milestone Target:</b> {tgt.strftime('%d %b %Y')}",
                        hoverinfo='text', showlegend=False, name=''
                    ))
                if plan:
                    fig_gantt.add_trace(go.Scatter(
                        x=[plan.strftime('%Y-%m-%d')], y=[label], mode='markers',
                        marker=dict(symbol='triangle-up', size=11,
                                    color='#22D3EE', line=dict(color='white', width=1)),
                        hovertext=f"<b>Plan Close:</b> {plan.strftime('%d %b %Y')}",
                        hoverinfo='text', showlegend=False, name=''
                    ))
                if actual:
                    fig_gantt.add_trace(go.Scatter(
                        x=[actual.strftime('%Y-%m-%d')], y=[label], mode='markers',
                        marker=dict(symbol='star', size=13,
                                    color='#4ADE80', line=dict(color='white', width=1)),
                        hovertext=f"<b>Actual Close:</b> {actual.strftime('%d %b %Y')}",
                        hoverinfo='text', showlegend=False, name=''
                    ))

            # ── TODAY line using add_shape with STRING x (fixes Timestamp bug) ──
            fig_gantt.add_shape(
                type='line',
                x0=TODAY_STR, x1=TODAY_STR,
                y0=0, y1=1, yref='paper',
                line=dict(color='#EF4444', dash='dash', width=2.5)
            )
            fig_gantt.add_annotation(
                x=TODAY_STR, y=1.02, yref='paper',
                text="<b>TODAY</b>", showarrow=False,
                font=dict(color='#EF4444', size=11),
                xanchor='center'
            )

            # Legend
            for sym, col, lbl in [
                ('circle',      col_set[0], 'Issue Start (color=Milestone)'),
                ('diamond',     '#FBBF24',  'Milestone Target'),
                ('triangle-up', '#22D3EE',  'Plan Close'),
                ('star',        '#4ADE80',  'Actual Close'),
            ]:
                fig_gantt.add_trace(go.Scatter(
                    x=[None], y=[None], mode='markers',
                    marker=dict(symbol=sym, size=10, color=col),
                    name=lbl, showlegend=True
                ))

            fig_gantt.update_layout(
                barmode='overlay',
                height=max(600, len(tl_df) * 24),
                template='plotly_dark',
                xaxis=dict(
                    type='date',
                    tickformat='%d %b %y',
                    range=['2025-11-01', '2026-05-01'],
                    title='Date', gridcolor='#1E293B'
                ),
                yaxis=dict(autorange='reversed', tickfont=dict(size=9), gridcolor='#1E293B'),
                margin=dict(l=10, r=20, t=55, b=40),
                legend=dict(
                    orientation='h', yanchor='bottom', y=1.01,
                    xanchor='right', x=1,
                    font=dict(size=10), bgcolor='rgba(0,0,0,0)'
                ),
                hoverlabel=dict(bgcolor='#1E293B', font_size=12, align='left'),
            )
            st.plotly_chart(fig_gantt, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 2 - World Map & Geography
    # ─────────────────────────────────────────────────────────────────────────
    with tab2:

        # Build per-country summary
        map_df = (fdf.groupby(['Country', 'Continent', 'ISO3'])
                     .agg(Issues=('Ser. No', 'count'),
                          Avg_Aging=('Aging', 'mean'))
                     .reset_index()
                     .dropna(subset=['ISO3']))
        map_df['Avg_Aging'] = map_df['Avg_Aging'].round(1)

        # MAP 1: Issue count choropleth
        st.subheader("World Map - Issue Count by Country")
        st.caption("Hover over any country to see issue count, continent and average aging.")

        fig_map1 = px.choropleth(
            map_df,
            locations='ISO3',
            color='Issues',
            hover_name='Country',
            hover_data={
                'Continent': True,
                'Issues':    True,
                'Avg_Aging': True,
                'ISO3':      False
            },
            color_continuous_scale='YlOrRd',
            projection='natural earth',
            template='plotly_dark',
            labels={'Issues': 'No. of Issues', 'Avg_Aging': 'Avg Aging (days)'},
        )
        fig_map1.update_geos(
            showcoastlines=True, coastlinecolor='#475569',
            showland=True,       landcolor='#1E293B',
            showocean=True,      oceancolor='#0F172A',
            showlakes=True,      lakecolor='#0F172A',
            showcountries=True,  countrycolor='#475569',
            showframe=False,
        )
        fig_map1.update_layout(
            height=560,
            margin=dict(l=0, r=0, t=20, b=0),
            coloraxis_colorbar=dict(
                title=dict(text='Issues', font=dict(color='white', size=11)),
                tickfont=dict(color='white', size=10),
                len=0.6, thickness=14,
            ),
            geo=dict(bgcolor='#0F172A'),
            paper_bgcolor='#0F172A',
            font=dict(color='white'),
            hoverlabel=dict(bgcolor='#1E293B', font_size=12, align='left'),
        )
        st.plotly_chart(fig_map1, use_container_width=True)

        # MAP 2: Avg Aging choropleth
        st.subheader("World Map - Average Aging (Days) by Country")
        st.caption("Red = high aging (issues open longer). Green = resolved quickly.")

        fig_map2 = px.choropleth(
            map_df,
            locations='ISO3',
            color='Avg_Aging',
            hover_name='Country',
            hover_data={
                'Continent': True,
                'Issues':    True,
                'Avg_Aging': True,
                'ISO3':      False
            },
            color_continuous_scale='RdYlGn_r',
            projection='natural earth',
            template='plotly_dark',
            labels={'Avg_Aging': 'Avg Aging (days)', 'Issues': 'No. of Issues'},
        )
        fig_map2.update_geos(
            showcoastlines=True, coastlinecolor='#475569',
            showland=True,       landcolor='#1E293B',
            showocean=True,      oceancolor='#0F172A',
            showlakes=True,      lakecolor='#0F172A',
            showcountries=True,  countrycolor='#475569',
            showframe=False,
        )
        fig_map2.update_layout(
            height=560,
            margin=dict(l=0, r=0, t=20, b=0),
            coloraxis_colorbar=dict(
                title=dict(text='Avg Aging', font=dict(color='white', size=11)),
                tickfont=dict(color='white', size=10),
                len=0.6, thickness=14,
            ),
            geo=dict(bgcolor='#0F172A'),
            paper_bgcolor='#0F172A',
            font=dict(color='white'),
            hoverlabel=dict(bgcolor='#1E293B', font_size=12, align='left'),
        )
        st.plotly_chart(fig_map2, use_container_width=True)

        # Country bar + Continent donut
        st.markdown("---")
        gcol1, gcol2 = st.columns(2)

        with gcol1:
            st.subheader("Issues by Country (Top 20)")
            country_cnt = (fdf.groupby('Country')['Ser. No']
                              .count().reset_index()
                              .rename(columns={'Ser. No': 'Count'})
                              .sort_values('Count', ascending=True)
                              .tail(20))
            fig_ctry = px.bar(
                country_cnt, y='Country', x='Count', orientation='h',
                labels={'Count': 'Number of Issues'},
                color='Count', color_continuous_scale='Blues',
                template='plotly_dark', text='Count'
            )
            fig_ctry.update_layout(
                height=max(420, len(country_cnt) * 22),
                yaxis=dict(tickfont=dict(size=9)),
                coloraxis_showscale=False
            )
            fig_ctry.update_traces(textposition='outside')
            st.plotly_chart(fig_ctry, use_container_width=True)

        with gcol2:
            st.subheader("Issues by Continent")
            cont_cnt = (fdf.groupby('Continent')['Ser. No']
                           .count().reset_index()
                           .rename(columns={'Ser. No': 'Count'}))
            cont_col_map = {c: CONTINENT_COLORS.get(c, ['#94A3B8'])[0]
                            for c in cont_cnt['Continent']}
            fig_donut = px.pie(
                cont_cnt, values='Count', names='Continent',
                hole=0.5, color='Continent',
                color_discrete_map=cont_col_map,
                template='plotly_dark'
            )
            fig_donut.update_traces(textposition='outside', textinfo='label+percent+value')
            st.plotly_chart(fig_donut, use_container_width=True, height=500)

        # Department bar
        st.subheader("Issues by Department")
        dept_cnt = (fdf.groupby('Department')['Ser. No']
                       .count().reset_index()
                       .rename(columns={'Ser. No': 'Count'})
                       .sort_values('Count', ascending=True))
        dept_col_map = {d: DEPT_COL.get(d, '#94A3B8') for d in dept_cnt['Department']}
        fig_dept = px.bar(
            dept_cnt, y='Department', x='Count', orientation='h',
            labels={'Count': 'Number of Issues'},
            color='Department', color_discrete_map=dept_col_map,
            template='plotly_dark', text='Count'
        )
        fig_dept.update_layout(
            showlegend=False, height=380,
            yaxis=dict(tickfont=dict(size=10))
        )
        fig_dept.update_traces(textposition='outside')
        st.plotly_chart(fig_dept, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 3 - Milestone & Correlations
    # ─────────────────────────────────────────────────────────────────────────
    with tab3:

        # Milestone grouped bar x continent
        st.subheader("Milestone Status x Continent (Grouped)")
        mile_cont = (fdf[fdf['Current Milestone'] != '']
                        .groupby(['Current Milestone', 'Continent'])['Ser. No']
                        .count().reset_index()
                        .rename(columns={'Ser. No': 'Count'}))
        mile_cont['Milestone Short'] = mile_cont['Current Milestone'].map(
            lambda x: MILE_SHORT.get(x, x)
        )
        cont_col_map2 = {c: CONTINENT_COLORS.get(c, ['#94A3B8'])[0]
                         for c in mile_cont['Continent'].unique()}
        fig_mg = px.bar(
            mile_cont, x='Milestone Short', y='Count',
            color='Continent', barmode='group',
            color_discrete_map=cont_col_map2,
            labels={'Count': 'No. of Issues', 'Milestone Short': 'Milestone'},
            template='plotly_dark', text='Count'
        )
        fig_mg.update_layout(xaxis_tickangle=-30, height=480)
        fig_mg.update_traces(textposition='outside')
        st.plotly_chart(fig_mg, use_container_width=True)

        # Plan vs Actual monthly
        st.subheader("Plan Close vs Actual Close - Monthly Comparison")
        plan_m   = (fdf['Closure Month - Plan']
                       .pipe(lambda s: pd.to_datetime(s, errors='coerce'))
                       .dt.to_period('M').value_counts().sort_index())
        actual_m = (fdf['Closure Month'].dt.to_period('M')
                       .value_counts().sort_index())
        all_p    = sorted(set(plan_m.index.tolist() + actual_m.index.tolist()))
        if all_p:
            pa_df = pd.DataFrame({
                'Month':  [str(p) for p in all_p],
                'Plan':   [plan_m.get(p, 0)   for p in all_p],
                'Actual': [actual_m.get(p, 0) for p in all_p],
            })
            fig_pa = go.Figure()
            fig_pa.add_trace(go.Bar(
                x=pa_df['Month'], y=pa_df['Plan'],
                name='Plan Close', marker_color='#22D3EE',
                text=pa_df['Plan'], textposition='outside'
            ))
            fig_pa.add_trace(go.Bar(
                x=pa_df['Month'], y=pa_df['Actual'],
                name='Actual Close', marker_color='#4ADE80',
                text=pa_df['Actual'], textposition='outside'
            ))
            fig_pa.update_layout(
                barmode='group', template='plotly_dark',
                xaxis_title='Month', yaxis_title='No. of Issues', height=430
            )
            st.plotly_chart(fig_pa, use_container_width=True)

        # Milestone donut
        st.subheader("Milestone Status Breakdown")
        mile_cnt = (fdf[fdf['Current Milestone'] != '']
                       .groupby('Current Milestone')['Ser. No']
                       .count().reset_index()
                       .rename(columns={'Ser. No': 'Count'})
                       .sort_values('Count', ascending=False))
        mile_col_map = {m: MILE_COL.get(m, '#94A3B8') for m in mile_cnt['Current Milestone']}
        fig_mile = px.pie(
            mile_cnt, values='Count', names='Current Milestone',
            hole=0.5, color='Current Milestone',
            color_discrete_map=mile_col_map,
            template='plotly_dark'
        )
        fig_mile.update_traces(
            textposition='outside', textinfo='percent+label',
            customdata=mile_cnt['Count'].values,
            hovertemplate='%{label}<br>Count: %{customdata}<extra></extra>'
        )
        st.plotly_chart(fig_mile, use_container_width=True, height=520)

        # HP Category bar
        st.subheader("Issues by HP Category")
        hp_cnt = (fdf.groupby('HP category')['Ser. No']
                     .count().reset_index()
                     .rename(columns={'Ser. No': 'Count'})
                     .sort_values('Count', ascending=False))
        fig_hp = px.bar(
            hp_cnt, x='HP category', y='Count',
            color='Count', color_continuous_scale='Cividis',
            labels={'Count': 'No. of Issues', 'HP category': 'HP Category'},
            text='Count', template='plotly_dark'
        )
        fig_hp.update_traces(textposition='outside')
        fig_hp.update_layout(coloraxis_showscale=False, height=420, xaxis_tickangle=-20)
        st.plotly_chart(fig_hp, use_container_width=True)

        # Aging scatter
        st.subheader("Aging vs No. of Failures - Scatter by Continent")
        sc_df = fdf.copy()
        sc_df['No of Failure Num'] = pd.to_numeric(
            sc_df['No of Failure'].astype(str).str.extract(r'(\d+)')[0],
            errors='coerce'
        )
        sc_df = sc_df.dropna(subset=['Aging', 'No of Failure Num'])
        if len(sc_df):
            fig_sc = px.scatter(
                sc_df, x='Aging', y='No of Failure Num',
                color='Continent',
                color_discrete_map={c: CONTINENT_COLORS.get(c, ['#94A3B8'])[0]
                                    for c in sc_df['Continent'].dropna().unique()},
                hover_data=['Ser. No', 'Issue Description', 'Country', 'Current Milestone'],
                labels={'Aging': 'Aging (Days)', 'No of Failure Num': 'No. of Failures'},

                template='plotly_dark', size_max=14
            )
            st.plotly_chart(fig_sc, use_container_width=True, height=480)

        # Correlation heatmap (identical structure to original)
        st.subheader("Correlation Heatmap - Numerical Features")
        if len(sc_df) and 'No of Failure Num' in sc_df.columns:
            num_df = sc_df[['Aging', 'No of Failure Num']].dropna()
            if len(num_df.columns) >= 2:
                corr = num_df.corr()
                fig_heat = go.Figure(data=go.Heatmap(
                    z=corr.values, x=corr.columns, y=corr.index,
                    colorscale='Twilight', zmid=0,
                    text=corr.round(2).values, hoverinfo='text'
                ))
                fig_heat.update_layout(
                    margin=dict(l=50, r=50, t=50, b=50),
                    xaxis_nticks=len(corr.columns),
                    yaxis_nticks=len(corr.index),
                    template='plotly_dark', height=380
                )
                st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    main()



