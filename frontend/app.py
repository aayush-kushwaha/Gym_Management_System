import streamlit as st
import requests 
import pandas as pd
import random
from datetime import datetime
import pytz

API_URL = "https://gym-management-system-ad16.onrender.com"
# API_URL = "http://127.0.0.1:8000"

# Page config
st.set_page_config(page_title="Gym Management System", page_icon="assets/favicon.jpg", layout="wide")

# Initialize session states
if 'admin_token' not in st.session_state:
    st.session_state.admin_token = None
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = None
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False
if 'show_admin_register' not in st.session_state:
    st.session_state.show_admin_register = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Function to handle admin login
def login(username, password):
    try:
        response = requests.post(f"{API_URL}/admin/login", data={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.admin_token = data["access_token"]
            st.session_state.admin_username = username
            st.rerun()
        else:
            st.error("Invalid credentials")
    except Exception as e:
        st.error(f"Login error: {str(e)}")

# Function to handle logout
def logout():
    st.session_state.admin_token = None
    st.session_state.admin_username = None
    st.rerun()

# Add greetings list at the top of the file after imports
greetings = [
    "Welcome, {name}! Let's make today a strong one! 💪🔥",
    "Hey, {name}! Time to crush your workout—let's get it! 🚀💥",
    "Welcome, {name}! You showed up—that's half the battle. Now let's win the rest! 🏆💯",
    "Welcome, {name}. Initiating workout mode… Let's power up! ⚡🤖",
    "Yo, {name}! The gym's waiting. Let's turn up the gains! 🏋️‍♂️🔥",
    "Welcome, {name}. Breathe in strength, exhale doubt. Let's move! 🧘‍♂️✨",
    "Welcome back, {name}! Your personal best is waiting to be broken today! 🎯🚴‍♂️"
]

# Function to mark attendance by ID
def mark_attendance_by_id(member_id):
    try:
        # Convert member_id to string and ensure it's in TDFC format
        member_id = str(member_id)
        if not member_id.startswith('TDFC'):
            member_id = f'TDFC{member_id.zfill(3)}'

        # Use the member_id with TDFC format
        response = requests.get(f"{API_URL}/members/verify_by_id/{member_id}")
        if response.status_code == 404:
            st.error("❌ Invalid Member ID")
            return False
        
        member = response.json()
        # Send data as query parameters
        params = {
            "member_code": member["member_code"],  # Use member_code instead of numeric ID
            "phone": member["phone"]
        }
        response = requests.post(f"{API_URL}/attendance/mark", params=params)
        
        if response.status_code == 200:
            greeting = random.choice(greetings).format(name=member["name"])
            st.success(greeting)
            st.balloons()
            return True
        elif response.status_code == 400:
            st.warning("⚠️ Attendance already marked for today")
            return False
        elif response.status_code == 403:
            st.error("❌ Your membership is inactive. Please contact the admin.")
            return False
        elif response.status_code == 404:
            st.error("❌ Invalid Member ID")
            return False
        else:
            st.error("❌ Failed to mark attendance")
            return False
    except Exception as e:
        st.error(f"Error marking attendance: {str(e)}")
        return False

# Function to mark attendance by name and phone
def mark_attendance(name, phone):
    try:
        # First verify member
        response = requests.get(f"{API_URL}/members/verify/{name}", params={"phone": phone})
        if response.status_code == 404:
            st.error("❌ User not found or not registered. Contact admin")
            return False
        
        member = response.json()
        # Use member_code instead of id
        response = requests.post(f"{API_URL}/attendance/mark", params={"member_id": member["member_code"], "phone": phone})
        if response.status_code == 200:
            greeting = random.choice(greetings).format(name=member["name"])
            st.success(greeting)
            st.balloons()
            return True
        elif response.status_code == 400:
            st.warning("⚠️ Attendance already marked for today")
            return False
        elif response.status_code == 403:
            st.error("❌ Your membership is inactive. Please contact the admin.")
            return False
        else:
            st.error("❌ Failed to mark attendance")
            return False
    except Exception as e:
        st.error(f"Error marking attendance: {str(e)}")
        return False

# Admin Login Sidebar Toggle
st.sidebar.markdown("## 2025 Gym Management System")

# Show login only if not logged in
if st.session_state.admin_token is None:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔑 Admin Login"):
            st.session_state.show_admin_login = not st.session_state.show_admin_login
            st.rerun()
    with col2:
        if st.button("📝 Register"):
            st.session_state.show_admin_register = True
            st.session_state.show_admin_login = False
            st.rerun()

    # Show Admin Login Form
    if st.session_state.show_admin_login:
        with st.sidebar.form("admin_login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            login_button = st.form_submit_button("🔓 Login")
            if login_button:
                login(username, password)
    
    # Show Admin Registration Form
    elif st.session_state.show_admin_register:
        with st.sidebar.form("admin_register_form"):
            st.subheader("📝 Admin Registration")
            new_username = st.text_input("👤 Username")
            new_password = st.text_input("🔑 Password", type="password")
            confirm_password = st.text_input("🔄 Confirm Password", type="password")
            register_button = st.form_submit_button("✅ Register")
            
            if register_button:
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters long!")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/admin/register",
                            json={"username": new_username, "password": new_password}
                        )
                        if response.status_code == 200:
                            st.success("✅ Admin registered successfully! You can now login.")
                            st.session_state.show_admin_register = False
                            st.session_state.show_admin_login = True
                            st.rerun()
                        elif response.status_code == 400:
                            st.error("❌ Username already exists!")
                        else:
                            st.error("❌ Registration failed!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# If logged in, show admin welcome message & logout button
if st.session_state.admin_token:
    st.sidebar.write(f"👋 Welcome, **{st.session_state.admin_username}**!")
    if st.sidebar.button("🚪 Logout"):
        logout()

    # Admin Dashboard Navigation
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")
    pages = [
        "📊 Dashboard",
        "👥 Members",
        "📝 Attendance",
        "💰 Payments"
    ]
    st.session_state.current_page = st.sidebar.radio("Go to", pages)

    # Main Content Area
    st.title(st.session_state.current_page)

    if st.session_state.current_page == "📊 Dashboard":
        # Dashboard Overview
        col1, col2, col3 = st.columns(3)
        
        try:
            # Fetch statistics
            headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
            
            # Get all members
            response = requests.get(f"{API_URL}/members/", headers=headers)
            if response.status_code == 200:
                members = response.json()
                active_members = len([m for m in members if m['membership_status']])
                
                with col1:
                    st.metric("Total Members", len(members))
                with col2:
                    st.metric("Active Members", active_members)
                with col3:
                    st.metric("Inactive Members", len(members) - active_members)

            # Get today's attendance
            response = requests.get(f"{API_URL}/attendance/today", headers=headers)
            if response.status_code == 200:
                today_attendance = response.json()
                st.subheader("Today's Check-ins")
                if today_attendance:
                    df = pd.DataFrame(today_attendance)
                    df['check_in_time'] = pd.to_datetime(df['check_in_time']).dt.strftime('%I:%M %p')
                    df['member_id'] = df.apply(lambda x: x['member']['member_code'] if x['member'] else x['member_id'], axis=1)
                    df = df[['id', 'member_id', 'check_in_time', 'check_out_time']]
                    df.columns = ['ID', 'Member ID', 'Check-in Time', 'Check-out Time']
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No check-ins recorded today")

        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")

    elif st.session_state.current_page == "👥 Members":
        # Members Management
        st.subheader("Member Management")
        
        # Add Member Form
        with st.expander("➕ Add New Member"):
            with st.form("add_member_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name")
                    phone = st.text_input("Phone Number")
                with col2:
                    membership_type = st.selectbox("Membership Type", ["Monthly", "Quarterly", "Yearly"])
                    member_code = st.text_input("Member Code (Optional)")
                
                submitted = st.form_submit_button("Add Member")
                if submitted:
                    try:
                        response = requests.post(
                            f"{API_URL}/members/",
                            headers={"Authorization": f"Bearer {st.session_state.admin_token}"},
                            json={
                                "name": name,
                                "phone": phone,
                                "membership_type": membership_type,
                                "member_code": member_code if member_code else None
                            }
                        )
                        if response.status_code == 200:
                            st.success("✅ Member added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add member")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Members List
        try:
            response = requests.get(
                f"{API_URL}/members/",
                headers={"Authorization": f"Bearer {st.session_state.admin_token}"}
            )
            if response.status_code == 200:
                members = response.json()
                if members:
                    df = pd.DataFrame(members)
                    df['membership_status'] = df['membership_status'].map({True: '✅ Active', False: '❌ Inactive'})
                    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
                    df = df[['member_code', 'name', 'phone', 'membership_type', 'membership_status', 'created_at']]
                    df.columns = ['Member ID', 'Name', 'Phone', 'Membership Type', 'Status', 'Join Date']
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No members found")
        except Exception as e:
            st.error(f"Error loading members: {str(e)}")

    elif st.session_state.current_page == "📝 Attendance":
        st.subheader("Attendance Records")
        try:
            response = requests.get(
                f"{API_URL}/attendance/today",
                headers={"Authorization": f"Bearer {st.session_state.admin_token}"}
            )
            if response.status_code == 200:
                attendances = response.json()
                if attendances:
                    df = pd.DataFrame(attendances)
                    df['member_id'] = df.apply(lambda x: x['member']['member_code'] if x['member'] else x['member_id'], axis=1)
                    df['check_in_time'] = pd.to_datetime(df['check_in_time']).dt.strftime('%Y-%m-%d %I:%M %p')
                    df = df[['id', 'member_id', 'check_in_time', 'check_out_time']]
                    df.columns = ['ID', 'Member ID', 'Check-in Time', 'Check-out Time']
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No attendance records found")
        except Exception as e:
            st.error(f"Error loading attendance: {str(e)}")

    elif st.session_state.current_page == "💰 Payments":
        st.subheader("Payment Records")
        # Add Payment Form
        with st.expander("💳 Record New Payment"):
            with st.form("add_payment_form"):
                col1, col2 = st.columns(2)
                with col1:
                    member_id = st.text_input("Member ID")
                    amount = st.number_input("Amount", min_value=0.0, format="%f")
                with col2:
                    next_due_date = st.date_input("Next Due Date")
                    payment_reference = st.text_input("Payment Reference")
                
                submitted = st.form_submit_button("Record Payment")
                if submitted:
                    try:
                        response = requests.post(
                            f"{API_URL}/payments/",
                            headers={"Authorization": f"Bearer {st.session_state.admin_token}"},
                            json={
                                "member_id": member_id,
                                "amount": amount,
                                "next_due_date": next_due_date.isoformat(),
                                "payment_reference": payment_reference
                            }
                        )
                        if response.status_code == 200:
                            st.success("✅ Payment recorded successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to record payment")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")


# If not logged in, show Attendance Form
# In the attendance form section, replace the current_time code with:
if not st.session_state.admin_token:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.image("https://i.imgur.com/SqPz1Mp.jpeg", width=300)
    
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    current_time = datetime.now(nepal_tz)
    st.markdown(f"<h3 style='text-align: center;'>{current_time.strftime('%A, %B %d, %Y')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>{current_time.strftime('%I:%M %p')}</h2>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🏋️‍♂️ Gym Check-in</h1>", unsafe_allow_html=True)

    # Create tabs for attendance marking and viewing
    tab1, tab2 = st.tabs(["📝 Mark Attendance", "📊 Today's Attendance"])

    with tab1:
        # Add verification method toggle with unique key
        verification_method = st.radio(
            "Select Verification Method",
            ["Name & Phone", "Member ID"],
            horizontal=True,
            key="verification_method_main"
        )

        with st.form("attendance_form"):
            if verification_method == "Name & Phone":
                name = st.text_input("👤 Full Name", key="attendance_name")
                phone = st.text_input("📱 Phone Number", key="attendance_phone")
                submit_disabled = not (name and len(name) >= 3 and phone and len(phone) == 10 and phone.isdigit())
            else:
                member_id = st.text_input("🆔 Member ID (e.g., TDFC001)", key="attendance_member_id")  # Updated example
                member_id = member_id.strip().upper()
    
            submitted = st.form_submit_button("✅ Mark Attendance")
    
            if submitted:
                if verification_method == "Name & Phone":
                    success = mark_attendance(name, phone)
                else:
                    if not member_id:
                        st.error("❌ Please enter a Member ID")
                        success = False
                    else:
                        try:
                            success = mark_attendance_by_id(member_id)  # Pass the full ID directly
                        except Exception:
                            st.error("❌ Invalid Member ID format. Please use format TDFC001")
                            success = False
                        if success:
                            st.session_state.form_submitted = True
                            st.rerun()
    
    with tab2:
        try:
            # Fetch today's attendance
            headers = {}
            if st.session_state.admin_token:
                headers["Authorization"] = f"Bearer {st.session_state.admin_token}"
                
            response = requests.get(f"{API_URL}/attendance/today", headers=headers)
            if response.status_code == 200:
                attendances = response.json()
                if attendances:
                    # Convert to DataFrame for better display
                    df = pd.DataFrame(attendances)
                    df['member_id'] = df['member_id'].apply(lambda x: f'TDFC{str(x).zfill(2)}')
                    df['check_in_time'] = pd.to_datetime(df['check_in_time']).dt.strftime('%I:%M %p')
                    df.columns = ['ID', 'Member ID', 'Check-in Time', 'Check-out Time']
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No attendance records for today.")
            elif response.status_code == 401:
                st.error("Authentication failed. Please log out and log in again.")
                # Clear token to force re-login
                st.session_state.admin_token = None
                st.rerun()
            else:
                st.error(f"Failed to fetch attendance records. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
        except Exception as e:
            st.error(f"Error fetching attendance: {str(e)}")
