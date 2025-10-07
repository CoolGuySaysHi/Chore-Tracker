import streamlit as st
import json, os
from datetime import datetime
import hashlib

# ---------------------------
# File paths
# ---------------------------
USER_FILE = "users.json"
COMPLETED_FILE = "completed.json"

# ---------------------------
# Helpers
# ---------------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored, provided):
    return stored == hash_password(provided)

# ---------------------------
# Load/save data
# ---------------------------
users = load_json(USER_FILE)
completed_data = load_json(COMPLETED_FILE)

def save_users(data):
    save_json(USER_FILE, data)

def save_completed():
    save_json(COMPLETED_FILE, completed_data)

# ---------------------------
# Weekly Summary + Sunday Reset
# ---------------------------
def auto_clear_and_bonus(user):
    today = datetime.now().strftime("%A")
    if today == "Sunday":
        user_data = users[user]
        last_bonus = user_data.get("last_bonus_date")
        today_str = datetime.now().strftime("%Y-%m-%d")

        if last_bonus != today_str:
            # Calculate weekly totals before reset
            week_total = sum(amt for _, amt, _ in st.session_state.completed)
            chores_done = len(st.session_state.completed)
            level_before = user_data.get("level_progress", 0)

            # Weekly summary popup
            st.info(f"🧾 **Weekly Summary:**\n\n"
                    f"- Total Earned This Week: £{week_total:.2f}\n"
                    f"- Chores Completed: {chores_done}\n"
                    f"- Level Progress Before Bonus: £{level_before:.2f}")

            # Add base pay bonus
            user_data["level_progress"] += user_data.get("base_amount", 0)
            user_data["last_bonus_date"] = today_str
            save_users(users)

            # Clear current chores
            st.session_state.completed = []
            save_completed()

            st.session_state["last_clear_date"] = today_str
            st.success("🎉 Weekly reset complete! Base amount added to your level and chores cleared.")

# ---------------------------
# App UI
# ---------------------------
st.set_page_config(page_title="Chore Tracker", page_icon="🧹", layout="centered")
st.title("🧹 Family Chore Tracker")

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# Login / Sign Up
# ---------------------------
if st.session_state.user is None:
    st.sidebar.header("Login / Create Account")
    choice = st.sidebar.radio("Choose Action:", ["Login", "Create Account"])

    if choice == "Login":
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user in users and verify_password(users[user]["password"], pw):
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid username or password.")

    else:
        new_user = st.text_input("Choose Username")
        new_pw = st.text_input("Choose Password", type="password")
        base_amt = st.number_input("Base Weekly Bonus (£)", min_value=0.0, step=0.1, value=1.7)
        if st.button("Create Account"):
            if new_user in users:
                st.error("That username already exists.")
            else:
                users[new_user] = {
                    "password": hash_password(new_pw),
                    "chores": [],
                    "base_amount": base_amt,
                    "total_earned": 0,
                    "level_progress": 0,
                    "level": 1,
                    "theme": "#0D1B4C",
                    "avatar": "",
                    "last_bonus_date": "",
                }
                save_users(users)
                completed_data[new_user] = {"completed": [], "history": []}
                save_completed()
                st.success("Account created! Please log in.")

# ---------------------------
# Main App for Logged-in User
# ---------------------------
if st.session_state.user:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as {user}")

    user_data = users[user]
    st.markdown(f"<h3 style='color:{user_data['theme']}'>Welcome back, {user}!</h3>", unsafe_allow_html=True)

    # Initialize session data
    if user not in completed_data:
        completed_data[user] = {"completed": [], "history": []}
        save_completed()

    if "completed" not in st.session_state:
        st.session_state.completed = completed_data[user]["completed"]

    # Sunday reset + bonus
    auto_clear_and_bonus(user)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🧾 Chores", "🏆 Progress", "⚙️ Settings"])

    # ---------------------------
    # CHORES TAB
    # ---------------------------
    with tab1:
        st.subheader("Your Chores")

        chores = user_data.get("chores", [])
        if "new_chore" not in st.session_state:
            st.session_state.new_chore = ""

        new_chore = st.text_input("Add a new chore:")
        amount = st.number_input("Reward (£)", min_value=0.0, step=0.1)
        if st.button("Add Chore"):
            if new_chore:
                chores.append({"name": new_chore, "amount": amount})
                users[user]["chores"] = chores
                save_users(users)
                st.success(f"Added chore '{new_chore}' (£{amount:.2f})")
                st.rerun()

        if chores:
            st.write("### Available Chores")
            for chore in chores:
                if st.button(f"✅ Complete: {chore['name']} (£{chore['amount']:.2f})", key=chore["name"]):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.completed.append([chore["name"], chore["amount"], timestamp])
                    completed_data[user]["completed"] = st.session_state.completed
                    completed_data[user]["history"].append([chore["name"], chore["amount"], timestamp])

                    users[user]["total_earned"] += chore["amount"]
                    users[user]["level_progress"] += chore["amount"]
                    save_users(users)
                    save_completed()
                    st.success(f"Chore '{chore['name']}' completed!")

        else:
            st.info("No chores yet! Add some above.")

        st.write("---")
        st.markdown("### ⚡ One-Off Chores")
        temp_chore = st.text_input("One-off Chore")
        temp_amount = st.number_input("One-off Reward (£)", min_value=0.0, step=0.1)
        if st.button("Complete One-off Chore"):
            if temp_chore:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.completed.append([temp_chore, temp_amount, timestamp])
                completed_data[user]["completed"] = st.session_state.completed
                completed_data[user]["history"].append([temp_chore, temp_amount, timestamp])
                users[user]["total_earned"] += temp_amount
                users[user]["level_progress"] += temp_amount
                save_users(users)
                save_completed()
                st.success(f"One-off chore '{temp_chore}' completed!")

        st.write("---")
        st.markdown("### 🧹 Current Completed Chores")
        if st.session_state.completed:
            for chore, amt, ts in st.session_state.completed:
                st.write(f"{ts} — {chore} (£{amt:.2f})")
        else:
            st.info("No chores completed this week.")

        if st.button("🗑️ Clear Current Completed Chores"):
            st.session_state.completed = []
            completed_data[user]["completed"] = []
            save_completed()
            st.success("Cleared current completed chores!")

        st.write("---")
        st.markdown("### 🏅 All-Time Completed Chores")
        if completed_data[user]["history"]:
            for chore, amt, ts in completed_data[user]["history"]:
                st.write(f"{ts} — {chore} (£{amt:.2f})")
        else:
            st.info("No historical chores yet.")

    # ---------------------------
    # PROGRESS TAB
    # ---------------------------
    with tab2:
        st.subheader("Your Progress")
        lvl = user_data.get("level", 1)
        prog = user_data.get("level_progress", 0)
        total = user_data.get("total_earned", 0)
        st.write(f"**Level:** {lvl}")
        st.write(f"**Total Earned:** £{total:.2f}")
        st.progress(min(prog % 10 / 10, 1.0))

        if prog >= lvl * 10:
            users[user]["level"] += 1
            users[user]["level_progress"] = 0
            save_users(users)
            st.success(f"🎉 Congrats {user}, you reached Level {users[user]['level']}!")

    # ---------------------------
    # SETTINGS TAB
    # ---------------------------
    with tab3:
        st.subheader("Settings")

        new_color = st.color_picker("Pick your theme color", user_data.get("theme", "#0D1B4C"))
        if st.button("Update Theme"):
            users[user]["theme"] = new_color
            save_users(users)
            st.success("Theme updated!")
            st.rerun()

        new_base = st.number_input("Change Base Weekly Bonus (£)", min_value=0.0, step=0.1, value=user_data.get("base_amount", 1.7))
        if st.button("Update Base Amount"):
            users[user]["base_amount"] = new_base
            save_users(users)
            st.success("Base amount updated!")
            st.rerun()

        st.markdown("---")
        st.subheader("Change Password")
        old_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if not verify_password(users[user]["password"], old_pw):
                st.error("Incorrect current password.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                users[user]["password"] = hash_password(new_pw)
                save_users(users)
                st.success("Password updated successfully!")

        st.markdown("---")
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
