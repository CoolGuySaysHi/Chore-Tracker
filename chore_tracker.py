import streamlit as st
from datetime import datetime
import json
import os

st.title("🧹 Chore Tracker with Money 💷")

# Base starting amount (like a salary)
BASE_AMOUNT = 1.70   # your base salary in pounds

# Chores with money values
chores = {
    "Take out the trash": 2.0,
    "Wash the dishes": 3.0,
    "Do the laundry": 5.0,
    "Vacuum the floor": 4.0
}

DATA_FILE = "completed_chores.json"

# Load completed chores from file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        st.session_state.completed = json.load(f)
else:
    st.session_state.completed = []

# Function to save completed chores to file
def save_completed():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.completed, f, indent=4)

# Display available chores
st.subheader("Available Chores")
for chore, amount in chores.items():
    if st.button(f"✅ {chore} (£{amount:.2f})"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.completed.append([chore, amount, timestamp])
        save_completed()

# Custom amount input
st.subheader("Custom Chore / Bonus")
custom_name = st.text_input("Chore/Task name", "")
custom_amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)

if st.button("➕ Add Custom Entry"):
    if custom_name and custom_amount > 0:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.completed.append([custom_name, custom_amount, timestamp])
        save_completed()
        st.success(f"Added {custom_name} (£{custom_amount:.2f})")

# Reset chores button
if st.button("🗑️ Clear Completed Chores"):
    st.session_state.completed = []
    save_completed()
    st.success("Completed chores have been cleared!")

# Display completed chores log
st.subheader("Completed Chores Log")
total_money = BASE_AMOUNT
st.markdown(f"**Starting Base: £{BASE_AMOUNT:.2f}**")

if st.session_state.completed:
    for c, amt, t in st.session_state.completed:
        st.write(f"{t} - {c} (£{amt:.2f})")
        total_money += amt

st.markdown(f"**Total Earned (Base + Chores): £{total_money:.2f}**")
