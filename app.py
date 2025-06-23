import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, date
import base64

# Streamlit page configuration
st.set_page_config(page_title="Guided Ambitions Client Tracker", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for pastel colors, gradient background, Arial font, and black text
st.markdown("""
    <style>
    /* Set global font to Arial and black text */
    html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox, .stDateInput, .stTextArea, .stButton, .stExpander, .stTabs {
        font-family: Arial, sans-serif !important;
        color: #000000 !important;
    }
    /* Gradient background */
    .stApp {
        background: linear-gradient(to bottom, #E6E6FA, #F5F5F5);
    }
    /* Style expanders (cards) */
    .stExpander {
        background-color: #E0FFF3;
        border: 1px solid #D3D3D3;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .stExpander > div > div {
        color: #000000 !important;
    }
    /* Style primary buttons */
    button[kind="primary"] {
        background-color: #ADD8E6 !important;
        color: #000000 !important;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
    }
    button[kind="primary"]:hover {
        background-color: #87CEEB !important;
        color: #000000 !important;
    }
    /* Style form inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #F5F5F5;
        border: 1px solid #D3D3D3;
        border-radius: 5px;
        color: #000000 !important;
    }
    /* Style headers */
    h1, h2, h3 {
        color: #000000 !important;
    }
    /* Style labels and placeholders */
    label, .stSelectbox > div > div > div, .stTextInput > div > div > div, .stDateInput > div > div > div, .stTextArea > div > div > div {
        color: #000000 !important;
    }
    /* Style tabs */
    .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #ADD8E6;
    }
    /* Center logo */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    /* Ensure success/error messages are readable */
    .stSuccess, .stError, .stWarning {
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load and encode logo
try:
    with open("logo.jpeg", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    logo_html = f'<div class="logo-container"><img src="data:image/jpeg;base64,{encoded_logo}" width="200"></div>'
    st.markdown(logo_html, unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("logo.jpeg not found. Please place it in the project directory.")

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
except FileNotFoundError:
    st.error("Error: credentials.json not found. Please place it in the project directory.")
    st.stop()

SHEET_ID = "1cFx2D5nzhBoYMek2zkqT4Qz8_fk16k4JG7sCSmuVRPo"

# Read data into Pandas DataFrame
@st.cache_data(ttl=60)
def load_data():
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet("Client Tracker")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Error: Spreadsheet not found. Check SHEET_ID or ensure the sheet is shared with the service account.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: Worksheet 'Client Tracker' not found in the spreadsheet.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Write updated row to Google Sheet
def update_row(row_index, updated_data):
    with st.spinner("Updating task..."):
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Client Tracker")
            sheet.update(f"A{row_index + 2}:Q{row_index + 2}", [updated_data.values.tolist()])
            sheet.update_cell(row_index + 2, 15, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except gspread.exceptions.WorksheetNotFound:
            st.error("Error: Worksheet 'Client Tracker' not found in the spreadsheet.")
            st.stop()
        except Exception as e:
            st.error(f"Error updating sheet: {str(e)}")
            st.stop()

# Append new row to Google Sheet
def add_row(new_data):
    with st.spinner("Adding new task..."):
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Client Tracker")
            sheet.append_row(new_data.values.tolist())
        except gspread.exceptions.WorksheetNotFound:
            st.error("Error: Worksheet 'Client Tracker' not found in the spreadsheet.")
            st.stop()
        except Exception as e:
            st.error(f"Error adding new task: {str(e)}")
            st.stop()

# Streamlit app
st.title("🎖️ Guided Ambitions Client Tracker")
st.markdown("Empowering veterans to transition to civilian careers or MBAs with streamlined task management.")

# Load data
df = load_data()

# Navigation tabs
tab1, tab2 = st.tabs(["View Clients", "Manage Tasks"])

# Tab 1: View Clients
with tab1:
    st.header("View Client Details")
    client_names = sorted(df["Client Name"].unique().tolist())
    selected_client = st.selectbox("Select Client", ["Select a client"] + client_names, key="client_select")
    
    if selected_client != "Select a client":
        client_df = df[df["Client Name"] == selected_client]
        st.subheader(f"Tasks for {selected_client}")
        
        # Display tasks in expandable cards
        for idx, row in client_df.iterrows():
            with st.expander(f"Task: {row['Task/Project']} (Status: {row['Status']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Phase**: {row['Phase']}")
                    st.markdown(f"**Priority**: {row['Priority']}")
                    st.markdown(f"**Start Date**: {row['Start Date'] or 'N/A'}")
                    st.markdown(f"**Due Date**: {row['Due Date'] or 'N/A'}")
                    st.markdown(f"**Follow-Up Date**: {row['Follow-Up Date'] or 'N/A'}")
                with col2:
                    st.markdown(f"**Email**: {row['Main Contact Email'] or 'N/A'}")
                    st.markdown(f"**Phone No.**: {row['Phone No.'] or 'N/A'}")
                    st.markdown(f"**Overdue?**: {row['Overdue?'] or 'No'}")
                    st.markdown(f"**Payment Status**: {row['Payment Status'] or 'Pending'}")
                st.markdown(f"**Notes**: {row['Notes/Call Log'] or 'N/A'}")
                st.markdown(f"**Drive Link**: [{row['Drive Link']}]({row['Drive Link']})" if row['Drive Link'] else "**Drive Link**: N/A")
                st.markdown(f"**Last Updated**: {row['Last Updated'] or 'N/A'}")

# Tab 2: Manage Tasks
with tab2:
    st.header("Manage Client Tasks")
    
    # Edit Existing Task
    st.subheader("Edit Existing Task")
    client_names = sorted(df["Client Name"].unique().tolist())
    edit_client = st.selectbox("Select Client to Edit", ["Select a client"] + client_names, key="edit_client_select")
    
    if edit_client != "Select a client":
        client_df = df[df["Client Name"] == edit_client]
        task_options = [f"{row['Task/Project']} (Status: {row['Status']})" for _, row in client_df.iterrows()]
        selected_task = st.selectbox("Select Task", ["Select a task"] + task_options, key="task_select")
        
        if selected_task != "Select a task":
            row_index = client_df.index[task_options.index(selected_task)]
            row_data = client_df.loc[row_index]
            
            with st.form("edit_task_form"):
                col1, col2 = st.columns(2)
                with col1:
                    client_name = st.text_input("Client Name", value=row_data["Client Name"], disabled=True)
                    email = st.text_input("Main Contact Email", value=row_data["Main Contact Email"])
                    phone_no = st.text_input("Phone No.", value=row_data["Phone No."])
                    task = st.text_input("Task/Project", value=row_data["Task/Project"])
                    phase = st.selectbox("Phase", options=["Profile Discovery", "Applications", "Initial Discovery"], index=["Profile Discovery", "Applications", "Initial Discovery"].index(row_data["Phase"]))
                    status = st.selectbox("Status", options=["Not Started", "In Progress", "Completed", "Waiting on Client"], index=["Not Started", "In Progress", "Completed", "Waiting on Client"].index(row_data["Status"]))
                with col2:
                    priority = st.selectbox("Priority", options=["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(row_data["Priority"]))
                    try:
                        start_date = st.date_input("Start Date", value=pd.to_datetime(row_data["Start Date"]).date() if row_data["Start Date"] else date.today())
                    except:
                        start_date = st.date_input("Start Date", value=date.today(), key="edit_start_date_fallback")
                    try:
                        due_date = st.date_input("Due Date", value=pd.to_datetime(row_data["Due Date"]).date() if row_data["Due Date"] else date.today())
                    except:
                        due_date = st.date_input("Due Date", value=date.today(), key="edit_due_date_fallback")
                    try:
                        follow_up_date = st.date_input("Follow-Up Date", value=pd.to_datetime(row_data["Follow-Up Date"]).date() if row_data["Follow-Up Date"] else date.today())
                    except:
                        follow_up_date = st.date_input("Follow-Up Date", value=date.today(), key="edit_follow_up_date_fallback")
                    payment_status = st.selectbox("Payment Status", options=["Pending", "Paid", "Overdue"], index=["Pending", "Paid", "Overdue"].index(row_data["Payment Status"] or "Pending"))
                    drive_link = st.text_input("Drive Link", value=row_data["Drive Link"])
                notes = st.text_area("Notes/Call Log", value=row_data["Notes/Call Log"], placeholder="e.g., Client interested in MBA applications")
                
                submitted = st.form_submit_button("Update Task", type="primary")
                if submitted:
                    updated_data = pd.Series({
                        "Record ID": row_data["Record ID"],
                        "Client Name": client_name,
                        "Main Contact Email": email,
                        "Phone No.": phone_no,
                        "Task/Project": task,
                        "Phase": phase,
                        "Status": status,
                        "Priority": priority,
                        "Start Date": start_date.strftime("%Y-%m-%d"),
                        "Due Date": due_date.strftime("%Y-%m-%d"),
                        "Follow-Up Date": follow_up_date.strftime("%Y-%m-%d"),
                        "Days to Due": (pd.to_datetime(due_date) - pd.to_datetime(datetime.now())).days,
                        "Overdue?": "Yes" if status != "Completed" and pd.to_datetime(due_date) < pd.to_datetime(datetime.now()) else "No",
                        "Notes/Call Log": notes,
                        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Drive Link": drive_link,
                        "Payment Status": payment_status
                    })
                    update_row(row_index, updated_data)
                    st.success(f"Task '{task}' for {client_name} updated successfully!")
                    st.cache_data.clear()

    # Add New Task
    st.subheader("Add New Task")
    with st.form("add_task_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_client = st.selectbox("Client Name", client_names, key="new_client_select")
            new_email = st.text_input("Main Contact Email")
            new_phone_no = st.text_input("Phone No.")
            new_task = st.text_input("Task/Project", placeholder="e.g., Resume Review")
            new_phase = st.selectbox("Phase", options=["Profile Discovery", "Applications", "Initial Discovery"], key="new_phase")
            new_status = st.selectbox("Status", options=["Not Started", "In Progress", "Completed", "Waiting on Client"], key="new_status")
        with col2:
            new_priority = st.selectbox("Priority", options=["High", "Medium", "Low"], key="new_priority")
            new_start_date = st.date_input("Start Date", value=date.today(), key="new_start_date")
            new_due_date = st.date_input("Due Date", value=date.today(), key="new_due_date")
            new_follow_up_date = st.date_input("Follow-Up Date", value=date.today(), key="new_follow_up_date")
            new_payment_status = st.selectbox("Payment Status", options=["Pending", "Paid", "Overdue"], key="new_payment_status")
            new_drive_link = st.text_input("Drive Link", placeholder="e.g., https://drive.google.com/folder/...")
        new_notes = st.text_area("Notes/Call Log", placeholder="e.g., Client interested in MBA applications")
        
        new_submitted = st.form_submit_button("Add Task", type="primary")
        if new_submitted:
            if not new_task:
                st.error("Task/Project is required.")
            else:
                new_record_id = f"REC_{len(df) + 1:04d}"
                new_data = pd.Series({
                    "Record ID": new_record_id,
                    "Client Name": new_client,
                    "Main Contact Email": new_email,
                    "Phone No.": new_phone_no,
                    "Task/Project": new_task,
                    "Phase": new_phase,
                    "Status": new_status,
                    "Priority": new_priority,
                    "Start Date": new_start_date.strftime("%Y-%m-%d"),
                    "Due Date": new_due_date.strftime("%Y-%m-%d"),
                    "Follow-Up Date": new_follow_up_date.strftime("%Y-%m-%d"),
                    "Days to Due": (pd.to_datetime(new_due_date) - pd.to_datetime(datetime.now())).days,
                    "Overdue?": "Yes" if new_status != "Completed" and pd.to_datetime(new_due_date) < pd.to_datetime(datetime.now()) else "No",
                    "Notes/Call Log": new_notes,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Drive Link": new_drive_link,
                    "Payment Status": new_payment_status
                })
                add_row(new_data)
                st.success(f"New task '{new_task}' for {new_client} added successfully!")
                st.cache_data.clear()

# Footer
st.markdown("---")
st.markdown("© 2025 Guided Ambitions. Built for veteran career transitions.", unsafe_allow_html=True)