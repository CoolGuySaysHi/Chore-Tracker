import streamlit as st
import json, os, hashlib
from datetime import datetime, timedelta
import pandas as pd
import math

st.set_page_config(page_title="Chore Tracker", page_icon="🧹", layout="centered")
THEME_COLOR = "#0D1B4C"

# ---------------------------
# Utility Functions
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password_attempt):
    return stored_hash == hash_password(password_attempt)

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def ensure_user_folder(user):
    os.makedirs(f"user_data/{user}", exist_ok=True)

# ---------------------------
# User-specific chores
# ---------------------------
def load_available_chores(user):
    path = f"user_data/{user}/available_chores.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    default = {
        "Take out the trash": 2.0,
        "Wash the dishes": 3.0,
        "Do the laundry": 5.0,
        "Vacuum the floor": 4.0
    }
    os.makedirs(f"user_data/{user}", exist_ok=True)
    with open(path, "w") as f:
        json.dump(default, f, indent=4)
    return default

def save_available_chores(user, data):
    os.makedirs(f"user_data/{user}", exist_ok=True)
    with open(f"user_data/{user}/available_chores.json", "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------
# Session setup
# ---------------------------
users = load_users()
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# Login / Signup
# ---------------------------
if st.session_state.user is None:
    st.title("🔐 Login to Chore Tracker")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and verify_password(users[username]["password"], password):
                st.session_state.user = username
                ensure_user_folder(username)
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        base_amount = st.number_input("Base Amount (£)", min_value=0.0, step=0.1, value=1.70)
        if st.button("Create Account"):
            if not new_user or not new_pass:
                st.warning("Enter a username and password.")
            elif new_user in users:
                st.error("Username already exists.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                users[new_user] = {
                    "password": hash_password(new_pass),
                    "base_amount": base_amount,
                    "theme": THEME_COLOR,
                    "avatar": None,
                    "level": 1
                }
                ensure_user_folder(new_user)
                load_available_chores(new_user)
                # Initialize history file
                history_file = f"user_data/{new_user}/completed_history.json"
                if not os.path.exists(history_file):
                    with open(history_file, "w") as f:
                        json.dump([], f)
                save_users(users)
                st.success(f"Account created with base pay £{base_amount:.2f}! Log in to continue.")

# ---------------------------
# Main App
# ---------------------------
else:
    user = st.session_state.user
    ensure_user_folder(user)
    st.title(f"🧹 {user}'s Chore Tracker")

    BASE_AMOUNT = users[user].get("base_amount", 1.70)
    AVATAR_PATH = users[user].get("avatar")
    DATA_FILE = f"user_data/{user}/completed_chores.json"         # Current UI list
    HISTORY_FILE = f"user_data/{user}/completed_history.json"    # Permanent record
    chores = load_available_chores(user)

    # Load current session completed
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            st.session_state.completed = json.load(f)
    else:
        st.session_state.completed = []

    # Load history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            st.session_state.completed_history = json.load(f)
    else:
        st.session_state.completed_history = []

    def save_completed():
        with open(DATA_FILE, "w") as f:
            json.dump(st.session_state.completed, f, indent=4)

    def save_completed_history():
        with open(HISTORY_FILE, "w") as f:
            json.dump(st.session_state.completed_history, f, indent=4)

    st.markdown(f"""
    <style>
    .stButton>button {{
        background-color: {THEME_COLOR};
        color: white;
        border-radius: 8px;
        border: none;
    }}
    .stButton>button:hover {{ opacity:0.9; }}
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏠 Chores", "📊 Summary", "⚙️ Settings"])

    # ---------------------------
    # Chores Tab
    # ---------------------------
    with tab1:
        if st.button("🚪 Log Out"):
            st.session_state.user = None
            st.rerun()

        if AVATAR_PATH and os.path.exists(AVATAR_PATH):
            st.image(AVATAR_PATH, width=100)

        st.subheader("Available Chores")
        for chore, amount in chores.items():
            col1, col2 = st.columns([4,1])
            with col1:
                if st.button(f"✅ {chore} (£{amount:.2f})", key=f"do_{chore}"):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.completed.append([chore, amount, timestamp])
                    st.session_state.completed_history.append([chore, amount, timestamp])
                    save_completed()
                    save_completed_history()
            with col2:
                if st.button("❌", key=f"del_{chore}"):
                    del chores[chore]
                    save_available_chores(user, chores)
                    st.rerun()

        st.subheader("Add New Chore")
        new_name = st.text_input("Chore name")
        new_amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)
        if st.button("➕ Add Chore"):
            if new_name and new_amount > 0:
                chores[new_name] = new_amount
                save_available_chores(user, chores)
                st.success(f"Added '{new_name}' (£{new_amount:.2f})!")
                st.rerun()

        st.subheader("Custom One-off Entry")
        custom_name = st.text_input("One-off task name", key="oneoff")
        custom_amount = st.number_input("One-off amount (£)", min_value=0.0, step=0.5, key="oneoff_amt")
        if st.button("➕ Add One-off"):
            if custom_name and custom_amount > 0:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.completed.append([custom_name, custom_amount, timestamp])
                st.session_state.completed_history.append([custom_name, custom_amount, timestamp])
                save_completed()
                save_completed_history()
                st.success(f"Added one-off: {custom_name} (£{custom_amount:.2f})")

        # Current vs All-Time boxes
        st.subheader("📋 Current Completed Chores")
        if st.session_state.completed:
            for chore, amt, ts in st.session_state.completed:
                st.write(f"{ts} — {chore} (£{amt:.2f})")
        else:
            st.info("No chores completed in the current session.")

        if st.button("🗑️ Clear Current Completed Chores"):
            st.session_state.completed = []
            save_completed()
            st.success("Current chores cleared from UI! All-time history is preserved.")

        st.subheader("📜 All-Time Completed Chores")
        if st.session_state.completed_history:
            for chore, amt, ts in st.session_state.completed_history:
                st.write(f"{ts} — {chore} (£{amt:.2f})")
        else:
            st.info("No historical chores recorded yet.")

    # ---------------------------
    # Summary Tab
    # ---------------------------
    with tab2:
        st.subheader("Earnings Summary")
        today = datetime.now()
        base_for_level = BASE_AMOUNT if today.weekday() == 4 else 0
        total_for_level = sum([amt for _, amt, _ in st.session_state.completed_history]) + base_for_level
        total_money = total_for_level

        st.markdown(f"**Total Earned (Including Base Pay): £{total_money:.2f}**")

        # Level
        level = math.floor(total_for_level / 10) + 1
        prev_threshold = (level - 1) * 10
        progress_amount = total_for_level - prev_threshold
        progress = max(min(progress_amount / 10, 1.0), 0.0)
        st.markdown(f"**Level:** {level}")
        st.progress(progress)

        if users[user].get("level", 1) != level:
            users[user]["level"] = level
            save_users(users)

        if today.weekday() != 4:
            st.info(f"Next base pay of £{BASE_AMOUNT:.2f} counts toward level this Friday!")

        # Graphs & achievements
        if st.session_state.completed_history:
            df = pd.DataFrame(st.session_state.completed_history, columns=["Chore","Amount","Timestamp"])
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df["Date"] = df["Timestamp"].dt.date

            st.write(f"**Last 7 Days:** £{df[df['Timestamp']>=today-timedelta(days=7)]['Amount'].sum():.2f}")
            st.write(f"**Last 30 Days:** £{df[df['Timestamp']>=today-timedelta(days=30)]['Amount'].sum():.2f}")

            daily_totals = df.groupby("Date")["Amount"].sum().reset_index()
            st.line_chart(daily_totals.set_index("Date"))

            st.divider()
            st.subheader("🏅 Achievements")
            total_done = len(df)
            badges = []
            if total_done>=5: badges.append("🥉 Bronze — 5 chores done")
            if total_done>=10: badges.append("🥈 Silver — 10 chores done")
            if total_done>=25: badges.append("🥇 Gold — 25 chores done")
            if total_done>=50: badges.append("🏆 Platinum — 50 chores done")
            if badges:
                for b in badges: st.write(b)
            else:
                st.info("Complete more chores to earn achievements!")

    # ---------------------------
    # Settings Tab
    # ---------------------------
    with tab3:
        st.subheader("User Settings")
        if AVATAR_PATH and os.path.exists(AVATAR_PATH):
            st.image(AVATAR_PATH,width=120)
        uploaded = st.file_uploader("Upload avatar", type=["png","jpg","jpeg"])
        if uploaded:
            path = f"user_data/{user}/avatar_{uploaded.name}"
            with open(path,"wb") as f: f.write(uploaded.getbuffer())
            users[user]["avatar"]=path
            save_users(users)
            st.success("Avatar updated!"); st.rerun()

        st.markdown("### 🎨 Theme Color")
        new_theme = st.color_picker("Pick your color", value=THEME_COLOR)
        if st.button("Update Theme Color"):
            users[user]["theme"]=new_theme; save_users(users); st.success(f"Theme updated to {new_theme}"); st.rerun()

        st.markdown("### 💷 Base Amount")
        new_base = st.number_input("Change Base (£)", min_value=0.0, step=0.1, value=BASE_AMOUNT)
        if st.button("Update Base Amount"):
            users[user]["base_amount"]=new_base; save_users(users); st.success(f"Base updated to £{new_base:.2f}"); st.rerun()

        st.markdown("### 🔑 Change Password")
        old_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if not verify_password(users[user]["password"], old_pass):
                st.error("Incorrect current password.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                users[user]["password"]=hash_password(new_pass); save_users(users); st.success("Password updated!")
