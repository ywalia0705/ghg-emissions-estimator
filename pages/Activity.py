import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🔍 Smart Activity Input")
st.sidebar.title("🧠 Input Activity")
st.title("🔍 Smart Activity Entry")
st.markdown("Enter an activity name and we'll identify its Scope and Category automatically.")

# Load emission factors
try:
    emission_factors = pd.read_csv("emission_factors.csv")
except FileNotFoundError:
    st.error("emission_factors.csv not found. Please ensure it's in the root folder.")
    st.stop()

# Initialize session state if not already
def init_session():
    if "emissions_log" not in st.session_state:
        st.session_state.emissions_log = []
    if "emissions_summary" not in st.session_state:
        st.session_state.emissions_summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}

init_session()

# Activity selection with autocomplete
activity = st.selectbox("Select or type an activity:", emission_factors["activity"].unique())

# Fetch associated details
data_row = emission_factors[emission_factors["activity"] == activity].iloc[0]
scope = data_row["scope"]
category = data_row.get("category", "-")
unit = data_row["unit"]
emission_factor = data_row["emission_factor"]

# Show identified details
st.info(f"Identified as: **{scope}** | Category: **{category}** | Unit: **{unit}** | Emission Factor: **{emission_factor}**")

# Quantity input
quantity = st.number_input(f"Enter quantity in {unit}", min_value=0.0, format="%.4f")

# Add to dashboard
if st.button("Add to Dashboard") and quantity > 0:
    emissions = quantity * emission_factor
    new_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Scope": scope,
        "Category": category,
        "Activity": activity,
        "Quantity": quantity,
        "Unit": unit,
        "Emission Factor": emission_factor,
        "Emissions (tCO₂e)": emissions
    }
    st.session_state.emissions_log.append(new_entry)

    # Update summary
    updated_summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}
    for entry in st.session_state.emissions_log:
        updated_summary[entry["Scope"]] += entry["Emissions (tCO₂e)"]
    st.session_state.emissions_summary = updated_summary

    st.success("Activity added to dashboard!")
