import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="GHG Emissions Estimator",
    page_icon="🌍",
    layout="wide"
)

with st.container():
    st.title("🌱 GHG Emissions Estimator")
    st.markdown("Estimate Scope 1, 2, and 3 emissions using activity data and emission factors.")

try:
    emission_factors = pd.read_csv("emission_factors.csv")
    st.success("Emission factors loaded successfully!")
except FileNotFoundError:
    st.error("emission_factors.csv not found. Please ensure it's in the same folder as app.py.")

if "emissions_summary" not in st.session_state:
    st.session_state.emissions_summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}

if "emissions_log" not in st.session_state:
    st.session_state.emissions_log = []

if st.sidebar.radio("Navigation", ["Dashboard", "Input data from CSV"], index=1) == "Input data from CSV":
    st.header("🧠 Smart Activity Input")
    st.markdown("Upload your activity data and let the tool match and categorize them automatically.")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        try:
            bulk_df = pd.read_csv(uploaded_file)
            required_columns = {"Scope", "Category", "Activity", "Quantity"}
            if not required_columns.issubset(bulk_df.columns):
                st.error(f"CSV must contain columns: {required_columns}")
            else:
                for _, row in bulk_df.iterrows():
                    scope = row["Scope"]
                    category = row.get("Category", "-")
                    activity = row["Activity"]
                    quantity = float(row["Quantity"])

                    match_df = emission_factors[
                        (emission_factors["scope"] == scope) &
                        (emission_factors["activity"] == activity)
                    ]
                    if scope == "Scope 3":
                        match_df = match_df[match_df["category"] == category]

                    if not match_df.empty:
                        unit = match_df["unit"].values[0]
                        ef = match_df["emission_factor"].values[0]
                        emissions = quantity * ef
                        entry = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Scope": scope,
                            "Category": category,
                            "Activity": activity,
                            "Quantity": quantity,
                            "Unit": unit,
                            "Emission Factor": ef,
                            "Emissions (tCO₂e)": emissions
                        }
                        st.session_state.emissions_log.append(entry)
                    else:
                        st.warning(f"No match found for {activity} in {scope} - {category}")

                summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}
                for e in st.session_state.emissions_log:
                    summary[e["Scope"]] += e["Emissions (tCO₂e)"]
                st.session_state.emissions_summary = summary
                st.success("Bulk upload processed successfully!")
        except Exception as e:
            st.error(f"Failed to process file: {e}")
else:
    with st.expander("📄 View Emission Factors Table"):
        st.dataframe(emission_factors)

    st.sidebar.header("Enter Your Activity Data")
    add_mode = st.sidebar.toggle("➕ Add Entry Mode", value=False)

    if add_mode:
        scope_options = emission_factors["scope"].unique()
        selected_scope = st.sidebar.selectbox("Select Scope", scope_options)
        filtered_df = emission_factors[emission_factors["scope"] == selected_scope]

        if selected_scope == "Scope 3":
            category_options = filtered_df["category"].dropna().unique()
            selected_category = st.sidebar.selectbox("Select Scope 3 Category", category_options)
            category_df = filtered_df[filtered_df["category"] == selected_category]
            activity_options = category_df["activity"].unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            unit = category_df[category_df["activity"] == selected_activity]["unit"].values[0]
            emission_factor = category_df[category_df["activity"] == selected_activity]["emission_factor"].values[0]
        else:
            selected_category = "-"
            activity_options = filtered_df["activity"].unique()
            selected_activity = st.sidebar.selectbox("Select Activity", activity_options)
            unit = filtered_df[filtered_df["activity"] == selected_activity]["unit"].values[0]
            emission_factor = filtered_df[filtered_df["activity"] == selected_activity]["emission_factor"].values[0]

        quantity = st.sidebar.number_input(f"Enter quantity ({unit}):", min_value=0.0, format="%.4f")

        if st.sidebar.button("Add Entry") and quantity > 0:
            emissions = quantity * emission_factor
            new_entry = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Scope": selected_scope,
                "Category": selected_category,
                "Activity": selected_activity,
                "Quantity": quantity,
                "Unit": unit,
                "Emission Factor": emission_factor,
                "Emissions (tCO₂e)": emissions
            }
            st.session_state.emissions_log.append(new_entry)

            updated_summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}
            for entry in st.session_state.emissions_log:
                updated_summary[entry["Scope"]] += entry["Emissions (tCO₂e)"]
            st.session_state.emissions_summary = updated_summary

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📅 Emission Summary")
        if st.session_state.emissions_log:
            latest = st.session_state.emissions_log[-1]
            st.markdown("**Latest Entry**")
            st.markdown(f"- Timestamp: {latest['Timestamp']}")
            st.markdown(f"- Scope: {latest['Scope']}")
            st.markdown(f"- Category: {latest['Category']}")
            st.markdown(f"- Activity: {latest['Activity']}")
            st.markdown(f"- Quantity: {latest['Quantity']:.4f} {latest['Unit']}")
            st.markdown(f"- Emission Factor: {latest['Emission Factor']}")
            st.markdown(f"- Emissions: {latest['Emissions (tCO₂e)']:.4f} tCO₂e")
        else:
            st.info("No entries yet. Add data from the sidebar.")

    with col2:
        st.subheader("📊 Emission Breakdown by Scope")
        chart_data = pd.DataFrame.from_dict(
            st.session_state.emissions_summary,
            orient="index",
            columns=["Emissions (tCO₂e)"]
        ).reset_index().rename(columns={"index": "Scope"})

        chart_data = chart_data[chart_data["Emissions (tCO₂e)"] > 0]

        if not chart_data.empty:
            fig = px.pie(
                chart_data,
                names="Scope",
                values="Emissions (tCO₂e)",
                color_discrete_sequence=px.colors.sequential.Purples_r,
                hole=0.45
            )
            fig.update_layout(
                height=400,
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title_text=""
            )
            st.plotly_chart(fig, use_container_width=True, key="emissions_chart")
        else:
            st.info("No data yet to show breakdown chart.")

    if st.session_state.emissions_log:
        st.markdown("### 📂 Emissions Log")

        log_df = pd.DataFrame(st.session_state.emissions_log)
        log_df.index = range(1, len(log_df) + 1)

        selected_rows = st.multiselect("Select rows to delete", options=log_df.index.tolist(), default=[])
        if st.button("Delete Selected Rows") and selected_rows:
            log_df = log_df.drop(index=selected_rows)
            st.session_state.emissions_log = log_df.to_dict(orient="records")

            updated_summary = {"Scope 1": 0, "Scope 2": 0, "Scope 3": 0}
            for _, row in log_df.iterrows():
                updated_summary[row["Scope"]] += row["Emissions (tCO₂e)"]
            st.session_state.emissions_summary = updated_summary

        total_row = pd.DataFrame([{
            "Timestamp": "-",
            "Scope": "Total",
            "Category": "-",
            "Activity": "-",
            "Quantity": log_df["Quantity"].sum(),
            "Unit": "",
            "Emission Factor": "-",
            "Emissions (tCO₂e)": log_df["Emissions (tCO₂e)"].sum()
        }])

        final_log_df = pd.concat([log_df, total_row], ignore_index=True)
        final_log_df.index = range(1, len(final_log_df) + 1)
        st.dataframe(final_log_df, use_container_width=True)
    else:
        st.info("No emissions log data to display.")
