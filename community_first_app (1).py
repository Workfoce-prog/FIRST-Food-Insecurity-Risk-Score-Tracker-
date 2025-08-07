
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

st.set_page_config(page_title="Community Food Insecurity Tracker", layout="wide")

st.title("🍎 Food Insecurity Risk Score Tracker – Community View")

# Upload form
with st.form("community_form"):
    name = st.text_input("Community Worker Name")
    region = st.selectbox("Region", ["North", "South", "East", "West", "Central"])
    date = st.date_input("Date", datetime.today())
    frl_rate = st.slider("Free/Reduced Lunch %", 0.0, 100.0, 50.0)
    attendance_rate = st.slider("Attendance Rate %", 0.0, 100.0, 85.0)
    unemployment_rate = st.slider("Unemployment Rate %", 0.0, 30.0, 8.0)
    eviction_notices = st.slider("Eviction Notices per 100 Households", 0, 100, 25)
    food_scarcity = st.slider("Food Scarcity Reports", 0, 100, 20)
    utility_shutoffs = st.slider("Utility Shutoffs", 0, 100, 15)
    notes = st.text_area("Additional Notes")

    submit = st.form_submit_button("📤 Submit Report")

# Save submission
if submit:
    entry = {
        "Worker": name,
        "Region": region,
        "Date": date.strftime("%Y-%m-%d"),
        "FRL": frl_rate,
        "Attendance": attendance_rate,
        "Unemployment": unemployment_rate,
        "Evictions": eviction_notices,
        "Food Scarcity": food_scarcity,
        "Shutoffs": utility_shutoffs,
        "Notes": notes
    }
    file_path = Path("community_submissions.csv")
    if file_path.exists():
        df = pd.read_csv(file_path)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:
        df = pd.DataFrame([entry])
    df.to_csv(file_path, index=False)
    st.success("✅ Submission saved successfully!")

# Display submissions
if Path("community_submissions.csv").exists():
    st.subheader("📊 Community Submissions Dashboard")
    df = pd.read_csv("community_submissions.csv")
    st.dataframe(df)

    region_counts = df["Region"].value_counts().reset_index()
    region_counts.columns = ["Region", "Reports"]
    chart = alt.Chart(region_counts).mark_bar().encode(
        x="Region", y="Reports", color="Region"
    )
    st.altair_chart(chart, use_container_width=True)
