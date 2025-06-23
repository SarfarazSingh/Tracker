import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
from datetime import datetime, date
import base64

# ─────────────────────────────── GOOGLE SHEETS ──────────────────────────────
# Service-account credentials are stored in the GOOGLE_SHEET_CREDS environment variable on Render,
# or in credentials.json locally for development.
# ─────────────────────────────────────────────────────────────────────────────

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Load credentials from environment variable, fallback to credentials.json locally
creds_dict = json.loads(os.getenv("GOOGLE_SHEET_CREDS", "{}"))
if not creds_dict:
    try:
        with open("credentials.json", "r") as f:
            creds_dict = json.load(f)
    except FileNotFoundError:
        st.error("credentials.json not found and GOOGLE_SHEET_CREDS not set. Please configure credentials.")
        st.stop()
    except json.JSONDecodeError:
        st.error("Invalid JSON format in credentials.json.")
        st.stop()

try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
except Exception as exc:
    st.error(f"Failed to authenticate with Google Sheets: {exc}")
    st.stop()

# Spreadsheet & worksheet
SHEET_ID = "1cFx2D5nzhBoYMek2zkqT4Qz8_fk16k4JG7sCSmuVRPo"
WS_NAME = "Client Tracker"

# [Rest of your existing code: PAGE SET-UP, CUSTOM STYLING, HELPERS, APP, FOOTER...]

# ──────────────────────────────── PAGE SET-UP ─────────────────────────────

st.set_page_config(
    page_title="Guided Ambitions Client Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CUSTOM STYLING -----------------------------

st.markdown(
    """
    <style>
        html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox,
        .stDateInput, .stTextArea, .stButton, .stExpander, .stTabs {
            font-family: Arial, sans-serif !important;
            color: #000000 !important;
        }
        .stApp {
            background: linear-gradient(to bottom, #E6E6FA, #F5F5F5);
        }
        .stExpander {
            background-color: #E0FFF3;
            border: 1px solid #D3D3D3;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        button[kind="primary"] {
            background-color: #ADD8E6 !important;
            color: #000000 !important;
            border: none; border-radius: 5px; padding: 8px 16px;
        }
        button[kind="primary"]:hover {
            background-color: #87CEEB !important;
        }
        .stTextInput input,
        .stSelectbox select,
        .stDateInput input,
        .stTextArea textarea {
            background-color: #F5F5F5;
            border: 1px solid #D3D3D3;
            border-radius: 5px;
            color: #000000 !important;
        }
        .logo-container {
            display: flex; justify-content: center; margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------- HEADER / LOGO ---------------------------

try:
    with open("logo.jpeg", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f'<div class="logo-container"><img src="data:image/jpeg;base64,{encoded_logo}" width="200"></div>',
        unsafe_allow_html=True,
    )
except FileNotFoundError:
    st.warning("logo.jpeg not found – skipping logo render.")

# ──────────────────────────────── HELPERS ─────────────────────────────────

@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    """Fetch worksheet into a DataFrame (cached 60 s)."""
    try:
        ws = client.open_by_key(SHEET_ID).worksheet(WS_NAME)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as exc:
        st.error(f"Error loading data: {exc}")
        st.stop()

def update_row(row_index: int, updated: pd.Series) -> None:
    """Write a Series back to the sheet (0-based index)."""
    with st.spinner("Updating task …"):
        ws = client.open_by_key(SHEET_ID).worksheet(WS_NAME)
        # +2 → header row + 1-based indexing
        ws.update(f"A{row_index+2}:Q{row_index+2}", [updated.tolist()])
        ws.update_cell(row_index+2, 15, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def add_row(new_row: pd.Series) -> None:
    """Append a new row to the sheet."""
    with st.spinner("Adding new task …"):
        ws = client.open_by_key(SHEET_ID).worksheet(WS_NAME)
        ws.append_row(new_row.tolist())

# ──────────────────────────────── APP MAIN ────────────────────────────────

st.title("🎖️ Guided Ambitions Client Monitor")
st.markdown("Empowering veterans to transition to civilian careers or MBAs with streamlined task management.")

df = load_data()

# -------------------------------- TABS -----------------------------------

tab_view, tab_manage = st.tabs(["View Clients", "Manage Tasks"])

# ▸▸ TAB 1 – VIEW Clients ▹▹

with tab_view:
    st.header("View Client Details")
    client_list = sorted(df["Client Name"].dropna().unique())
    sel_client = st.selectbox("Select Client", ["— choose —"] + client_list)

    if sel_client != "— choose —":
        client_df = df[df["Client Name"] == sel_client]
        st.subheader(f"Tasks for {sel_client}")

        for _, row in client_df.iterrows():
            with st.expander(f"Task: {row['Task/Project']} (Status: {row['Status']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Phase**: {row['Phase']}")
                    st.markdown(f"**Priority**: {row['Priority']}")
                    st.markdown(f"**Start Date**: {row['Start Date'] or 'N/A'}")
                    st.markdown(f"**Due Date**: {row['Due Date'] or 'N/A'}")
                    st.markdown(f"**Follow-Up**: {row['Follow-Up Date'] or 'N/A'}")
                with col2:
                    st.markdown(f"**Email**: {row['Main Contact Email'] or 'N/A'}")
                    st.markdown(f"**Phone**: {row['Phone No.'] or 'N/A'}")
                    st.markdown(f"**Overdue?**: {row['Overdue?'] or 'No'}")
                    st.markdown(f"**Payment**: {row['Payment Status'] or 'Pending'}")
                st.markdown(f"**Notes**: {row['Notes/Call Log'] or '—'}")
                if row['Drive Link']:
                    st.markdown(f"**Drive**: [{row['Drive Link']}]({row['Drive Link']})")
                st.markdown(f"**Last Updated**: {row['Last Updated'] or '—'}")

# ▸▸ TAB 2 – MANAGE Tasks ▹▹

with tab_manage:
    st.header("Manage Client Tasks")

    # ---------- EDIT Existing Task ----------
    st.subheader("Edit Existing Task")
    edit_client = st.selectbox("Client", ["— choose —"] + client_list, key="edit_client")

    if edit_client != "— choose —":
        tasks_df = df[df["Client Name"] == edit_client]
        task_labels = [f"{r['Task/Project']} (Status: {r['Status']})" for _, r in tasks_df.iterrows()]
        sel_task = st.selectbox("Task", ["— choose —"] + task_labels, key="edit_task")

        if sel_task != "— choose —":
            idx = tasks_df.index[task_labels.index(sel_task)]
            record = tasks_df.loc[idx]

            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Client Name", value=record["Client Name"], disabled=True)
                    email = st.text_input("Email", value=record["Main Contact Email"])
                    phone = st.text_input("Phone", value=record["Phone No."])
                    task = st.text_input("Task/Project", value=record["Task/Project"])
                    phase = st.selectbox("Phase", ["Profile Discovery", "Applications", "Initial Discovery"], 
                                        index=["Profile Discovery", "Applications", "Initial Discovery"].index(record["Phase"]))
                    status = st.selectbox("Status", ["Not Started", "In Progress", "Completed", "Waiting on Client"], 
                                         index=["Not Started", "In Progress", "Completed", "Waiting on Client"].index(record["Status"]))
                with col2:
                    priority = st.selectbox("Priority", ["High", "Medium", "Low"], 
                                          index=["High", "Medium", "Low"].index(record["Priority"]))
                    start_date = st.date_input("Start", value=pd.to_datetime(record["Start Date"], errors="coerce").date() if pd.notnull(record["Start Date"]) else date.today())
                    due_date = st.date_input("Due", value=pd.to_datetime(record["Due Date"], errors="coerce").date() if pd.notnull(record["Due Date"]) else date.today())
                    follow_date = st.date_input("Follow-Up", value=pd.to_datetime(record["Follow-Up Date"], errors="coerce").date() if pd.notnull(record["Follow-Up Date"]) else date.today())
                    payment = st.selectbox("Payment", ["Pending", "Paid", "Overdue"], 
                                          index=["Pending", "Paid", "Overdue"].index(record["Payment Status"] or "Pending"))
                    drive = st.text_input("Drive Link", value=record["Drive Link"])
                notes = st.text_area("Notes/Call Log", value=record["Notes/Call Log"], key="edit_notes")

                if st.form_submit_button("Update", type="primary"):
                    updated = pd.Series({
                        "Record ID": record["Record ID"],
                        "Client Name": record["Client Name"],
                        "Main Contact Email": email,
                        "Phone No.": phone,
                        "Task/Project": task,
                        "Phase": phase,
                        "Status": status,
                        "Priority": priority,
                        "Start Date": start_date.strftime("%Y-%m-%d"),
                        "Due Date": due_date.strftime("%Y-%m-%d"),
                        "Follow-Up Date": follow_date.strftime("%Y-%m-%d"),
                        "Days to Due": (pd.to_datetime(due_date) - datetime.now()).days,
                        "Overdue?": "Yes" if status != "Completed" and pd.to_datetime(due_date) < datetime.now() else "No",
                        "Notes/Call Log": notes,
                        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Drive Link": drive,
                        "Payment Status": payment,
                    })
                    update_row(idx, updated)
                    st.success("Task updated ✓")
                    st.cache_data.clear()

    # ---------- ADD New Task ----------
    st.subheader("Add New Task")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_name = st.selectbox("Client", client_list, key="new_client")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            task = st.text_input("Task/Project")
            phase = st.selectbox("Phase", ["Profile Discovery", "Applications", "Initial Discovery"], key="new_phase")
            status = st.selectbox("Status", ["Not Started", "In Progress", "Completed", "Waiting on Client"], key="new_status")
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="new_priority")
            start_date = st.date_input("Start", value=date.today(), key="new_start")
            due_date = st.date_input("Due", value=date.today(), key="new_due")
            follow_date = st.date_input("Follow-Up", value=date.today(), key="new_follow")
            payment = st.selectbox("Payment", ["Pending", "Paid", "Overdue"], key="new_payment")
            drive = st.text_input("Drive Link", key="new_drive")
        notes = st.text_area("Notes/Call Log", key="new_notes")

        if st.form_submit_button("Add", type="primary"):
            if not task:
                st.error("Task/Project is required.")
            elif not c_name:
                st.error("Client Name is required.")
            else:
                new_id = f"REC_{len(df)+1:04d}"
                new_row = pd.Series({
                    "Record ID": new_id,
                    "Client Name": c_name,
                    "Main Contact Email": email,
                    "Phone No.": phone,
                    "Task/Project": task,
                    "Phase": phase,
                    "Status": status,
                    "Priority": priority,
                    "Start Date": start_date.strftime("%Y-%m-%d"),
                    "Due Date": due_date.strftime("%Y-%m-%d"),
                    "Follow-Up Date": follow_date.strftime("%Y-%m-%d"),
                    "Days to Due": (pd.to_datetime(due_date) - datetime.now()).days,
                    "Overdue?": "Yes" if status != "Completed" and pd.to_datetime(due_date) < datetime.now() else "No",
                    "Notes/Call Log": notes,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Drive Link": drive,
                    "Payment Status": payment,
                })
                add_row(new_row)
                st.success("Task added ✓")
                st.cache_data.clear()

# -------------------------------- FOOTER -----------------------------------

st.markdown("---")
st.caption("© 2025 Guided Ambitions – Built for veteran career transitions.")
