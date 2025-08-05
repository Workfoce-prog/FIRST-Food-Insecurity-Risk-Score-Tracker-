
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Community FIRST Risk Tracker", layout="wide")

st.title("🍎 Food Insecurity Risk Score Tracker (Community Version)")
st.markdown("Upload household-level data to assess food insecurity risk using basic intake information.")

REQUIRED_COLUMNS = [
    "FRL_Status", "SNAP_Use", "Unemployed", "Pantry_Use", 
    "Utility_Shutoff_Risk", "Housing_Instability"
]

st.download_button(
    label="📥 Download Sample CSV Template",
    data=','.join(["Household_ID", "Zip_Code"] + REQUIRED_COLUMNS) + "\n1001,62208,1,1,0,1,0,0",
    file_name="Community_FIRST_Template.csv",
    mime="text/csv"
)

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_cols:
        st.error(f"❌ The following required columns are missing: {', '.join(missing_cols)}")
    else:
        # Compute risk score and level
        df["Risk_Score"] = df[REQUIRED_COLUMNS].sum(axis=1) * 15

        def categorize(score):
            if score >= 90:
                return "Critical"
            elif score >= 70:
                return "High"
            elif score >= 40:
                return "Medium"
            else:
                return "Low"

        df["Risk_Level"] = df["Risk_Score"].apply(categorize)

        st.success("✅ Risk scores calculated successfully!")

        # Show scored data
        st.dataframe(df)

        # Visualization
        st.subheader("📊 Household Risk Level Distribution")
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Risk_Level:N", title="Risk Level"),
            y=alt.Y("count():Q", title="Number of Households"),
            color="Risk_Level:N"
        ).properties(width=600)
        st.altair_chart(chart)

        # Allow download of results
        st.download_button(
            label="⬇️ Download Scored Results",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="FIRST_Scored_Output.csv",
            mime="text/csv"
        )

st.caption("StratDesign Solutions – Community FIRST Demo Tool")
