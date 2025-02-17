import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

API_URL = "http://localhost:8000"

# Page config with custom CSS
st.set_page_config(page_title="Gym Management System", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for authentication
if 'admin_token' not in st.session_state:
    st.session_state.admin_token = None
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = None

def login(username, password):
    try:
        response = requests.post(
            f"{API_URL}/admin/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.admin_token = data["access_token"]
            st.session_state.admin_username = username
            return True
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def logout():
    st.session_state.admin_token = None
    st.session_state.admin_username = None

def get_dashboard_metrics(headers):
    try:
        # Get members
        response = requests.get(f"{API_URL}/members/", headers=headers)
        members = response.json() if response.status_code == 200 else []
        total_members = len(members)
        active_members = len([m for m in members if m.get('membership_status', False)])
        
        # Get today's attendance
        today = datetime.now().date()
        attendance_response = requests.get(f"{API_URL}/attendance/today", headers=headers)
        today_attendance = len(attendance_response.json()) if attendance_response.status_code == 200 else 0
        
        return {
            "total_members": total_members,
            "active_members": active_members,
            "today_attendance": today_attendance
        }
    except Exception as e:
        st.error(f"Error fetching metrics: {str(e)}")
        return {"total_members": 0, "active_members": 0, "today_attendance": 0}

# Display title
st.title("🏋️‍♂️ Gym Management System")

# Login/Logout in sidebar
st.sidebar.title("Admin Panel")
if st.session_state.admin_token is None:
    with st.sidebar.form("login_form"):
        st.write("Please login to continue")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if login(username, password):
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")
else:
    st.sidebar.write(f"Welcome, {st.session_state.admin_username}!")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

# Only show navigation if logged in
if st.session_state.admin_token:
    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    
    # Navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Members", "Attendance", "Payments"])

    if page == "Dashboard":
        # Get metrics
        metrics = get_dashboard_metrics(headers)
        
        # Display metrics in cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Total Members</div>
                </div>
            """.format(metrics["total_members"]), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Active Members</div>
                </div>
            """.format(metrics["active_members"]), unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Today's Attendance</div>
                </div>
            """.format(metrics["today_attendance"]), unsafe_allow_html=True)

        # Quick Actions
        st.subheader("Quick Actions")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("➕ Add New Member"):
                st.session_state.page = "Members"
                st.rerun()
                
        with quick_col2:
            if st.button("✓ Mark Attendance"):
                st.session_state.page = "Attendance"
                st.rerun()
                
        with quick_col3:
            if st.button("💰 Record Payment"):
                st.session_state.page = "Payments"
                st.rerun()

        # Recent Activity
        st.subheader("Recent Activity")
        try:
            # Get recent members
            recent_members = requests.get(f"{API_URL}/members/", headers=headers).json()[:5]
            if recent_members:
                st.markdown("**Latest Members**")
                member_df = pd.DataFrame(recent_members)
                st.dataframe(member_df[["name", "phone", "membership_type", "membership_status"]], use_container_width=True)
            
            # Get recent attendance
            recent_attendance = requests.get(f"{API_URL}/attendance/recent", headers=headers).json()[:5]
            if recent_attendance:
                st.markdown("**Recent Attendance**")
                attendance_df = pd.DataFrame(recent_attendance)
                st.dataframe(attendance_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading recent activity: {str(e)}")

    elif page == "Members":
        st.header("Member Management")
        
        with st.form("new_member_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name")
                phone = st.text_input("Phone")
            with col2:
                membership_type = st.selectbox(
                    "Membership Type",
                    ["monthly", "quarterly", "yearly"]
                )
            
            if st.form_submit_button("Add Member"):
                try:
                    response = requests.post(
                        f"{API_URL}/members/",
                        json={
                            "name": name,
                            "phone": phone,
                            "membership_type": membership_type,
                        },
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success("Member added successfully!")
                    else:
                        st.error("Failed to add member")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # Display members
        try:
            response = requests.get(f"{API_URL}/members/", headers=headers)
            if response.status_code == 200:
                members = response.json()
                if members:
                    df = pd.DataFrame(members)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No members found")
        except Exception as e:
            st.error(f"Error fetching members: {str(e)}")

    elif page == "Attendance":
        st.header("Attendance Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Mark Attendance")
            member_id = st.number_input("Member ID", min_value=1, step=1)
            if st.button("Mark Attendance"):
                try:
                    response = requests.post(
                        f"{API_URL}/attendance/?member_id={member_id}",
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success("Attendance marked successfully!")
                    else:
                        st.error("Failed to mark attendance")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("View Attendance")
            view_member_id = st.number_input("Enter Member ID", min_value=1, step=1)
            if st.button("View Attendance"):
                try:
                    response = requests.get(
                        f"{API_URL}/attendance/{view_member_id}",
                        headers=headers
                    )
                    if response.status_code == 200:
                        records = response.json()
                        if records:
                            df = pd.DataFrame(records)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No attendance records found")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    elif page == "Payments":
        st.header("Payment Management")
        
        with st.form("payment_form"):
            col1, col2 = st.columns(2)
            with col1:
                member_id = st.number_input("Member ID", min_value=1, step=1)
                amount = st.number_input("Amount", min_value=0.0, step=100.0)
            with col2:
                next_due_date = st.date_input("Next Due Date")
            
            if st.form_submit_button("Record Payment"):
                try:
                    response = requests.post(
                        f"{API_URL}/payments/",
                        json={
                            "member_id": member_id,
                            "amount": amount,
                            "next_due_date": next_due_date.isoformat(),
                        },
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success("Payment recorded successfully!")
                    else:
                        st.error("Failed to record payment")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
else:
    st.info("Please login to access the system.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(" 2025 Gym Management System")
