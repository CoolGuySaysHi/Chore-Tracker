import streamlit as st
from datetime import datetime
import json
import os
import hashlib

st.set_page_config(page_title="Chore Tracker", page_icon="🧹", layout="centered")

# ---------------------------
# Utility Functions
# ---------------------------

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password_attempt):
    """Verify a password attempt"""
    return stored_hash == hash_password(password_attempt)

def load_users():
    """Load users from file"""
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to file"""
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def load_available_chores():
    """Load chores from shared file"""
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

# ---------------------------
# Login & Account Handling
# ---------------------------

users = load_users()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Login to Chore Tracker")

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    # --- Login tab ---
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in users and verify_password(users[username]["password"], password):
                st.session_state.user = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    # --- Create Account tab ---
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
                    "base_amount": base_amount
                }
                save_users(users)
                st.success(f"Account created with base pay of £{base_amount:.2f}! You can now log in.")

else:
    # ---------------------------
    # Main App for Logged-in User
    # ---------------------------
    st.title(f"🧹 {st.session_state.user}'s Chore Tracker 💷")

    user = st.session_state.user
    BASE_AMOUNT = users[user].get("base_amount", 1.70)

    # File for this user's completed chores
    DATA_FILE = f"completed_chores_{user}.json"

    # Shared file for available chores
    CHORES_FILE = "available_chores.json"

    # Load chores
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

    # Logout
    if st.button("🚪 Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- Available Chores ---
    st.subheader("Available Chores")
    for chore, amount in chores.items():
        col1, col2 = st.columns([4,1])
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

    # --- Add new available chore ---
    st.subheader("Add New Chore")
    new_chore_name = st.text_input("Chore name")
    new_chore_amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)

    if st.button("➕ Add to Available Chores"):
        if new_chore_name and new_chore_amount > 0:
            chores[new_chore_name] = new_chore_amount
            save_chores()
            st.success(f"Added '{new_chore_name}' (£{new_chore_amount:.2f}) to available chores!")
            st.rerun()

    # --- Custom One-off Entry ---
    st.subheader("Custom One-off Entry")
    custom_name = st.text_input("One-off chore/task name", key="oneoff")
    custom_amount = st.number_input("One-off amount (£)", min_value=0.0, step=0.5, key="oneoff_amt")

    if st.button("➕ Add One-off Entry"):
        if custom_name and custom_amount > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.completed.append([custom_name, custom_amount, timestamp])
            save_completed()
            st.success(f"Added one-off: {custom_name} (£{custom_amount:.2f})")

    # --- Reset Completed ---
    if st.button("🗑️ Clear Completed Chores"):
        st.session_state.completed = []
        save_completed()
        st.success("Completed chores have been cleared!")

    # --- Completed Chores Log ---
    st.subheader("Completed Chores Log")
    total_money = BASE_AMOUNT
    st.markdown(f"**Starting Base: £{BASE_AMOUNT:.2f}**")

    if st.session_state.completed:
        for c, amt, t in st.session_state.completed:
            st.write(f"{t} - {c} (£{amt:.2f})")
            total_money += amt

    st.markdown(f"**Total Earned (Base + Chores): £{total_money:.2f}**")
