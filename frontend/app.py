import streamlit as st
import requests
import pandas as pd
import random
from datetime import datetime

API_URL = "http://localhost:8000"

# Page config
st.set_page_config(page_title="Gym Management System", page_icon="assets/dragon_fitness_logo.jpg", layout="wide")

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
        # Use the member_id directly since it's already in the correct format
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

# If not logged in, show Attendance Form
if not st.session_state.admin_token:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.image("assets/dragon_fitness_logo.jpg", width=500)
    
    current_time = datetime.now()
    st.markdown(f"<h3 style='text-align: center;'>{current_time.strftime('%A, %B %d, %Y')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>{current_time.strftime('%I:%M %p')}</h2>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🏋️‍♂️ Gym Check-in</h1>", unsafe_allow_html=True)

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

# Admin Dashboard
if st.session_state.admin_token:
    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}

    # Navigation
    st.session_state.current_page = st.sidebar.radio(
        "📱 Navigation",
        ["📊 Dashboard", "👥 Members", "✅ Attendance", "💰 Payments"],
        index=["📊 Dashboard", "👥 Members", "✅ Attendance", "💰 Payments"].index(st.session_state.current_page),
    )

    # Dashboard Page
    if st.session_state.current_page == "📊 Dashboard":
        st.header("📊 Dashboard")
        st.write("Overview of gym statistics and attendance metrics.")
    
    # Members Page
    elif st.session_state.current_page == "👥 Members":
        st.header("👥 Member Management")
        with st.form("new_member_form"):
            name = st.text_input("Name")
            phone = st.text_input("Phone")
            member_code = st.text_input("Member Code (Optional)")  # Add member code field
            membership_type = st.selectbox("Membership Type", ["monthly", "quarterly", "yearly"])
            submit = st.form_submit_button("Add Member")
            if submit:
                try:
                    data = {
                        "name": name.strip(),
                        "phone": phone.strip(),
                        "member_code": member_code.strip(),  # Include member code
                        "membership_type": membership_type,
                        "membership_status": True
                    }
                    response = requests.post(
                        f"{API_URL}/members/", 
                        json=data,
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success("Member added successfully!")
                        st.rerun()
                    else:
                        error_detail = response.json().get("detail", "Failed to add member")
                        st.error(f"Failed to add member: {error_detail}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # In the Members Page section, update the display members list part
        # Display Members List
        st.subheader("📋 Members List")
        try:
            response = requests.get(f"{API_URL}/members/", headers=headers)
            if response.status_code == 200:
                members = response.json()
                if members:
                    # Convert to DataFrame for better display
                    df = pd.DataFrame(members)
                    # Reorder and rename columns
                    df = df[['id', 'name', 'phone', 'membership_type', 'membership_status', 'created_at']]
                    df.columns = ['ID', 'Name', 'Phone', 'Membership Type', 'Active', 'Joined Date']
                    # Format the date
                    df['Joined Date'] = pd.to_datetime(df['Joined Date']).dt.strftime('%Y-%m-%d')
                    # Convert boolean to Yes/No
                    df['Active'] = df['Active'].map({True: '✅ Yes', False: '❌ No'})
                    # Format ID with TDFC prefix
                    df['ID'] = df['ID'].apply(lambda x: f'TDFC{str(x).zfill(3)}')
                    
                    # Add delete buttons
                    for index, row in df.iterrows():
                        cols = st.columns([2, 2, 2, 2, 1, 1.5, 0.5])
                        cols[0].write(row['ID'])
                        cols[1].write(row['Name'])
                        cols[2].write(row['Phone'])
                        cols[3].write(row['Membership Type'])
                        cols[4].write(row['Active'])
                        cols[5].write(row['Joined Date'])
                        if cols[6].button('🗑️', key=f"delete_{row['ID']}", help="Delete member"):
                            if st.session_state.admin_token:
                                try:
                                    delete_response = requests.delete(
                                        f"{API_URL}/members/{row['ID']}", 
                                        headers=headers
                                    )
                                    if delete_response.status_code == 200:
                                        st.success(f"Member {row['Name']} deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete member")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                else:
                    st.info("No members registered yet.")
            else:
                st.error("Failed to fetch members list")
        except Exception as e:
            st.error(f"Error fetching members: {str(e)}")

    # Attendance Page
    elif st.session_state.current_page == "✅ Attendance":
        st.header("✅ Attendance Management")
        
        # Add tabs for different views
        tab1, tab2 = st.tabs(["📝 Mark Attendance", "📊 Attendance History"])
        
        with tab1:
            # Reuse the same attendance form logic with admin privileges
            verification_method = st.radio(
                "Select Verification Method",
                ["Name & Phone", "Member ID"],
                horizontal=True,
                key="verification_method_admin"
            )

            with st.form("admin_attendance_form"):
                if verification_method == "Name & Phone":
                    name = st.text_input("👤 Full Name", key="admin_attendance_name")
                    phone = st.text_input("📱 Phone Number", key="admin_attendance_phone")
                    submit_disabled = not (name and len(name) >= 3 and phone and len(phone) == 10 and phone.isdigit())
                else:
                    member_id = st.text_input("🆔 Member ID (e.g., TDFC01)", key="admin_attendance_member_id")
                    submit_disabled = not (member_id and member_id.startswith("TDFC") and len(member_id) >= 6 and member_id[4:].isdigit())

                # submitted = st.form_submit_button("✅ Mark Attendance", disabled=submit_disabled)
                submitted = st.form_submit_button("✅ Mark Attendance")

                if submitted:
                    if verification_method == "Name & Phone":
                        success = mark_attendance(name, phone)
                    else:
                        numeric_id = int(member_id[4:])
                        success = mark_attendance_by_id(numeric_id)
                    if success:
                        st.session_state.form_submitted = True
                        st.rerun()
        
        with tab2:
            try:
                # Fetch today's attendance
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
