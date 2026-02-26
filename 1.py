import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import numpy as np

# ---------- CONFIGURATION ----------
SHEET_ID = "TWS_Issue_Dashboard_Template.xlsx"               # Replace with your Google Sheet ID
SHEET_NAME = "Data"                       # Name of the sheet/tab
CREDS_FILE = "credentials.json"            # Downloaded JSON file

# ---------- CONNECT TO GOOGLE SHEETS ----------
@st.cache_data(ttl=600)  # Cache data for 10 minutes; remove if you want real-time on every refresh
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Convert date columns
    date_cols = ['DateOpened', 'DateClosed', 'PlannedMonth', 'ActualMonth']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Add DaysOpen helper column
    today = pd.Timestamp.now().normalize()
    df['DaysOpen'] = np.where(
        df['DateClosed'].isna(),
        (today - df['DateOpened']).dt.days,
        (df['DateClosed'] - df['DateOpened']).dt.days
    )
    return df

df = load_data()

# ---------- DASHBOARD TITLE ----------
st.set_page_config(layout="wide")
st.markdown(
    f"<h2 style='text-align: center;'>Issue Reported from {df['DateOpened'].min().strftime('%d-%b-%y')} to {df['DateOpened'].max().strftime('%d-%b-%y')} | Status as on {datetime.today().strftime('%d-%b-%Y')}</h2>",
    unsafe_allow_html=True
)

# ---------- TOP SUMMARY NUMBERS (from your CSV) ----------
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])
with col1:
    st.metric("Total No. of Issues", len(df))
with col2:
    closed_count = df[df['Status'] == 'Closed'].shape[0]
    st.metric("Total No. of Issues Closed", closed_count)
with col3:
    st.metric("Closure note make", 0)   # Placeholder – modify if you track this
with col4:
    st.metric("Total issue CN make along with pdf", 0)
with col5:
    st.metric("Total print done for Sign off", 0)

st.markdown("---")

# ---------- LAYOUT: LEFT SIDE (Overall Summary) & RIGHT SIDE (Table) ----------
left_col, right_col = st.columns([1, 2.5])

with left_col:
    st.subheader("Overall Summary")
    st.markdown("**Total Concern Report**")
    
    # Left side metrics (from your image)
    def left_metric(label, value):
        st.markdown(f"**{label}**")
        st.markdown(f"<h3 style='margin-top:-15px;'>{value}</h3>", unsafe_allow_html=True)
    
    left_metric("Unique Service Issue", df[df['Category'] == 'Service']['ID'].nunique())
    
    # Closed as on latest date
    latest_close_date = df['DateClosed'].max()
    closed_on_date = df[df['DateClosed'] == latest_close_date].shape[0] if pd.notna(latest_close_date) else 0
    left_metric("Closed as on Date", closed_on_date)
    
    balance_open = df[df['DateClosed'].isna()].shape[0]
    left_metric("Balance Open Issue", balance_open)
    
    # Under RCA + Service Information + Supplier action (customize as needed)
    under_rca_service = df[(df['Status'] == 'Under RCA') | (df['Category'] == 'Service')]['ID'].nunique()
    left_metric("Under RCA + Service Information + Supplier action", under_rca_service)
    
    rnd_plan_awaited = df[df['Status'] == 'R&D Plan Awaited'].shape[0]
    left_metric("R&D Plan Awaited", rnd_plan_awaited)
    
    # After Mar-2026 Implementation
    after_mar = df[df['PlannedMonth'] > pd.Timestamp('2026-03-31')].shape[0]
    left_metric("After Mar-2026 Implementation", after_mar)
    
    # Aging buckets
    open_df = df[df['DateClosed'].isna()]
    buckets = {
        "Below 30 HP": (open_df['DaysOpen'] < 30).sum(),
        "30 - 60 HP": ((open_df['DaysOpen'] >= 30) & (open_df['DaysOpen'] <= 60)).sum(),
        "60 - 101 HP": ((open_df['DaysOpen'] >= 60) & (open_df['DaysOpen'] <= 101)).sum(),
        "Above 101 HP": (open_df['DaysOpen'] > 101).sum(),
    }
    for label, value in buckets.items():
        left_metric(label, value)

with right_col:
    st.subheader("Implementation Plan V/s Actual Status")
    
    # Prepare data for the right table
    # We'll create a DataFrame that mimics the structure in your image
    table_data = {
        "Update on Date": ["Total Unique Issue", "Closed", "Cut off Awaited", "Under RCA - CFT",
                           "Service Responsibility", "Assembly Responsibility", "R&D Responsibility",
                           "Purchase Responsibility", "IQC Responsibility", "Implementation Plan",
                           "Actual Done", "Below 30 HP", "30 - 60 HP", "60 - 101 HP", "Above 101 HP",
                           "Total Issue"],
        "Total": [
            df['ID'].nunique(),
            df[df['Status'] == 'Closed'].shape[0],
            df[df['Status'] == 'Cut-off Awaited'].shape[0],
            df[df['Status'] == 'Under RCA - CFT'].shape[0],
            df[df['Responsibility'] == 'Service'].shape[0],
            df[df['Responsibility'] == 'Assembly'].shape[0],
            df[df['Responsibility'] == 'R&D'].shape[0],
            df[df['Responsibility'] == 'Purchase'].shape[0],
            df[df['Responsibility'] == 'IQC'].shape[0],
            "",  # Implementation Plan row has numbers in month columns
            "",  # Actual Done row has numbers in month columns
            buckets["Below 30 HP"],
            buckets["30 - 60 HP"],
            buckets["60 - 101 HP"],
            buckets["Above 101 HP"],
            len(df)
        ],
        "Under RCA": ["", "", "", "", "", "", "", "", "", 0, "", "", "", "", "", ""],
        "Jan-26": [
            "", "", "", "", "", "", "", "", "",
            df[(df['PlannedMonth'] >= '2026-01-01') & (df['PlannedMonth'] <= '2026-01-31')].shape[0],
            df[(df['ActualMonth'] >= '2026-01-01') & (df['ActualMonth'] <= '2026-01-31')].shape[0],
            "", "", "", "", ""
        ],
        "Feb-26": [
            "", "", "", "", "", "", "", "", "",
            df[(df['PlannedMonth'] >= '2026-02-01') & (df['PlannedMonth'] <= '2026-02-28')].shape[0],
            df[(df['ActualMonth'] >= '2026-02-01') & (df['ActualMonth'] <= '2026-02-28')].shape[0],
            "", "", "", "", ""
        ],
        "Mar-26": [
            "", "", "", "", "", "", "", "", "",
            df[(df['PlannedMonth'] >= '2026-03-01') & (df['PlannedMonth'] <= '2026-03-31')].shape[0],
            df[(df['ActualMonth'] >= '2026-03-01') & (df['ActualMonth'] <= '2026-03-31')].shape[0],
            "", "", "", "", ""
        ],
        "Apr-26": [
            "", "", "", "", "", "", "", "", "",
            df[(df['PlannedMonth'] >= '2026-04-01') & (df['PlannedMonth'] <= '2026-04-30')].shape[0],
            df[(df['ActualMonth'] >= '2026-04-01') & (df['ActualMonth'] <= '2026-04-30')].shape[0],
            "", "", "", "", ""
        ],
        "R&D will share the Plan": ["", "", "", "", "", "", "", "", "", 0, "", "", "", "", "", ""],
        "Remark": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    }
    
    table_df = pd.DataFrame(table_data)
    
    # Display as a static table (you can also use st.dataframe with styling)
    st.dataframe(table_df, use_container_width=True, hide_index=True)

# ---------- DOWNLOAD BUTTON ----------
st.markdown("---")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Raw Data as CSV",
    data=csv,
    file_name=f"dashboard_data_{datetime.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

