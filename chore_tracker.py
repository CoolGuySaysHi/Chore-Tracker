import streamlit as st
from datetime import datetime
import json
import os
import hashlib
from pathlib import Path

st.set_page_config(page_title="Chore Tracker", page_icon="🧹", layout="centered")

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

def load_available_chores():
    if os.path.exists("available_chores.json"):
        with open("available_chores.json", "r") as f:
            return json.load(f)
    default = {
        "Take out the trash": 2.0,
        "Wash the dishes": 3.0,
        "Do the laundry": 5.0,
        "Vacuum the floor": 4.0
    }
    with open("available_chores.json", "w") as f:
        json.dump(default, f, indent=4)
    return default

def ensure_user_folder(user):
    Path(f"user_data/{user}").mkdir(parents=True, exist_ok=True)

# ---------------------------
# Login & Account Handling
# ---------------------------

users = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

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
                st.warning("Please enter a username and password.")
            elif new_user in users:
                st.error("That username already exists.")
            elif new_pass != confirm_pass:
                st.error("Passwords don’t match.")
            else:
                users[new_user] = {
                    "password": hash_password(new_pass),
                    "base_amount": base_amount,
                    "theme": "#4CAF50",  # default green
                    "avatar": None
                }
                ensure_user_folder(new_user)
                save_users(users)
                st.success(f"Account created with base pay of £{base_amount:.2f}! You can now log in.")

else:
    # ---------------------------
    # Main App for Logged-in User
    # ---------------------------
    user = st.session_state.user
    ensure_user_folder(user)
    st.title(f"🧹 {user}'s Chore Tracker")

    BASE_AMOUNT = users[user].get("base_amount", 1.70)
    THEME_COLOR = users[user].get("theme", "#4CAF50")
    AVATAR_PATH = users[user].get("avatar")

    DATA_FILE = f"user_data/{user}/completed_chores.json"
    CHORES_FILE = "available_chores.json"

    chores = load_available_chores()

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            st.session_state.completed = json.load(f)
    else:
        st.session_state.completed = []

    def save_completed():
        with open(DATA_FILE, "w") as f:
            json.dump(st.session_state.completed, f, indent=4)

    def save_chores():
        with open(CHORES_FILE, "w") as f:
            json.dump(chores, f, indent=4)

    st.markdown(
        f"""
        <style>
        .stButton>button {{
            background-color: {THEME_COLOR};
            color: white;
            border-radius: 8px;
            border: none;
        }}
        .stButton>button:hover {{
            opacity: 0.9;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🏠 Chores", "🧾 Summary", "⚙️ Settings"])

    # ---------------------------
    # 🏠 Chores Tab
    # ---------------------------
    with tab1:
        if st.button("🚪 Log Out"):
            st.session_state.user = None
            st.rerun()

        if AVATAR_PATH and os.path.exists(AVATAR_PATH):
            st.image(AVATAR_PATH, width=100)
        st.subheader("Available Chores")
        for chore, amount in chores.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"✅ {chore} (£{amount:.2f})", key=f"do_{chore}"):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.completed.append([chore, amount, timestamp])
                    save_completed()
            with col2:
                if st.button("❌", key=f"del_{chore}"):
                    del chores[chore]
                    save_chores()
                    st.rerun()

        st.subheader("Add New Chore")
        new_chore_name = st.text_input("Chore name")
        new_chore_amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)

        if st.button("➕ Add to Available Chores"):
            if new_chore_name and new_chore_amount > 0:
                chores[new_chore_name] = new_chore_amount
                save_chores()
                st.success(f"Added '{new_chore_name}' (£{new_chore_amount:.2f})!")
                st.rerun()

        st.subheader("Custom One-off Entry")
        custom_name = st.text_input("One-off chore/task name", key="oneoff")
        custom_amount = st.number_input("One-off amount (£)", min_value=0.0, step=0.5, key="oneoff_amt")

        if st.button("➕ Add One-off Entry"):
            if custom_name and custom_amount > 0:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.completed.append([custom_name, custom_amount, timestamp])
                save_completed()
                st.success(f"Added one-off: {custom_name} (£{custom_amount:.2f})")

        if st.button("🗑️ Clear Completed Chores"):
            st.session_state.completed = []
            save_completed()
            st.success("Completed chores cleared!")

    # ---------------------------
    # 🧾 Summary Tab
    # ---------------------------
    with tab2:
        st.subheader("Completed Chores Log")
        total_money = BASE_AMOUNT
        st.markdown(f"**Starting Base: £{BASE_AMOUNT:.2f}**")

        if st.session_state.completed:
            for c, amt, t in st.session_state.completed:
                st.write(f"{t} - {c} (£{amt:.2f})")
                total_money += amt

        st.markdown(f"**Total Earned (Base + Chores): £{total_money:.2f}**")

    # ---------------------------
    # ⚙️ Settings Tab
    # ---------------------------
    with tab3:
        st.subheader("User Settings")

        if AVATAR_PATH and os.path.exists(AVATAR_PATH):
            st.image(AVATAR_PATH, width=120)
        uploaded_avatar = st.file_uploader("Upload new profile picture", type=["png", "jpg", "jpeg"])
        if uploaded_avatar:
            avatar_path = f"user_data/{user}/avatar_{uploaded_avatar.name}"
            with open(avatar_path, "wb") as f:
                f.write(uploaded_avatar.getbuffer())
            users[user]["avatar"] = avatar_path
            save_users(users)
            st.success("Profile picture updated!")
            st.rerun()

        st.markdown("### 🎨 Theme Color")
        new_theme = st.color_picker("Pick your color", value=THEME_COLOR)
        if st.button("Update Theme Color"):
            users[user]["theme"] = new_theme
            save_users(users)
            st.success(f"Theme color updated to {new_theme}")
            st.rerun()

        st.markdown("### 💷 Base Amount")
        new_base = st.number_input("Change Base (£)", min_value=0.0, step=0.1, value=BASE_AMOUNT)
        if st.button("Update Base Amount"):
            users[user]["base_amount"] = new_base
            save_users(users)
            st.success(f"Base updated to £{new_base:.2f}")
            st.rerun()

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
                users[user]["password"] = hash_password(new_pass)
                save_users(users)
                st.success("Password updated successfully!")
