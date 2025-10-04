import streamlit as st
from datetime import datetime
import json
import os

st.title("🧹 Chore Tracker with Money 💷")

# Base starting amount
BASE_AMOUNT = 2.00   # base salary in pounds

# File for completed chores
DATA_FILE = "completed_chores.json"

# File for available chores
CHORES_FILE = "available_chores.json"

# Chores with money values
default_chores = {
    "Empty Recycle Bins": 0.40,
    "Empty Dishwasher": 0.40,
    "Washing Car": 2.00,
    "Pairing Socks": 0.40
}

# Load available chores
if os.path.exists(CHORES_FILE):
    with open(CHORES_FILE, "r") as f:
        chores = json.load(f)
else:
    chores = default_chores
    with open(CHORES_FILE, "w") as f:
        json.dump(chores, f, indent=4)

# Load completed chores
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        st.session_state.completed = json.load(f)
else:
    st.session_state.completed = []

# Function to save completed chores
def save_completed():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.completed, f, indent=4)

# Function to save available chores
def save_chores():
    with open(CHORES_FILE, "w") as f:
        json.dump(chores, f, indent=4)

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
            st.experimental_rerun()

# --- Add New Available Chore ---
st.subheader("Add New Chore")
new_chore_name = st.text_input("Chore name")
new_chore_amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)

if st.button("➕ Add to Available Chores"):
    if new_chore_name and new_chore_amount > 0:
        chores[new_chore_name] = new_chore_amount
        save_chores()
        st.success(f"Added '{new_chore_name}' (£{new_chore_amount:.2f}) to available chores!")
        st.experimental_rerun()

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
